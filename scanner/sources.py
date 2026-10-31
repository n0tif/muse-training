"""Sumber posting: API X atau berkas dari browser. Keduanya hanya membaca."""

from __future__ import annotations

import json
import time
from pathlib import Path

from scanner.config import ScanConfig
from scanner.http_util import HttpRequest, HttpResponse, Transport
from scanner.models import Post

SEARCH_URL = "https://api.x.com/2/tweets/search/recent"


class SourceError(RuntimeError):
    pass


def search_queries(config: ScanConfig) -> list[str]:
    queries = []
    for text in config.queries:
        queries.append(_with_retweet_filter(text, config.exclude_retweets))
    for account in config.accounts:
        queries.append(_with_retweet_filter(f"from:{account}", config.exclude_retweets))
    return queries


def _with_retweet_filter(text: str, exclude_retweets: bool) -> str:
    if exclude_retweets and "-is:retweet" not in text:
        return f"({text}) -is:retweet"
    return text


class XSearchClient:
    def __init__(self, token: str, transport: Transport, sleep=time.sleep, now=time.time) -> None:
        self.token = token
        self.transport = transport
        self.sleep = sleep
        self.now = now

    def search_page(self, query: str, max_results: int, page_token: str | None = None) -> tuple[list[Post], str | None]:
        params = {
            "query": query,
            "max_results": str(max_results),
            "tweet.fields": "id,text,created_at,author_id,entities",
            "expansions": "author_id",
            "user.fields": "id,username,created_at,public_metrics",
        }
        if page_token:
            params["next_token"] = page_token
        delay = 1.0
        last_status = 0
        for _ in range(5):
            response = self.transport.send(
                HttpRequest(
                    method="GET",
                    url=SEARCH_URL,
                    headers={
                        "authorization": f"Bearer {self.token}",
                        "user-agent": "muse-training-scanner/1.0",
                    },
                    params=params,
                )
            )
            last_status = response.status
            if response.status == 429:
                self.sleep(_retry_delay(response, self.now, delay))
                delay = min(delay * 2, 60)
                continue
            if response.status != 200:
                snippet = response.body.decode("utf-8", "replace")[:180].replace(self.token, "[redacted]")
                raise SourceError(f"HTTP {response.status} {snippet}")
            payload = response.json()
            if not isinstance(payload, dict):
                raise SourceError("balasan pencarian bukan objek")
            return _posts_from_search(payload), _next_token(payload)
        raise SourceError(f"batas laju API masih aktif setelah beberapa percobaan ({last_status})")


def fetch_api_posts(config: ScanConfig, client: XSearchClient) -> list[Post]:
    found: list[Post] = []
    seen: set[str] = set()
    for query in search_queries(config):
        page = None
        for _ in range(config.max_pages):
            posts, page = client.search_page(query, config.max_results, page)
            for post in posts:
                if post.id in seen:
                    continue
                seen.add(post.id)
                found.append(post)
                if len(found) >= config.max_posts:
                    return found
            if not page:
                break
    return found


def load_posts(path: Path) -> list[Post]:
    if not path.is_file():
        raise SourceError(f"berkas posting tidak ada: {path.name}")
    raw = path.read_text(encoding="utf-8")
    stripped = raw.lstrip()
    if path.suffix.lower() == ".json" or stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = None
        if data is not None:
            return _posts_from_user_json(data)
    return _posts_from_text(raw)


def _retry_delay(response: HttpResponse, now, fallback: float) -> float:
    retry_after = response.headers.get("retry-after")
    if retry_after:
        try:
            return min(180.0, max(0.0, float(retry_after)))
        except ValueError:
            pass
    reset = response.headers.get("x-rate-limit-reset")
    if reset:
        try:
            return min(180.0, max(0.0, float(reset) - float(now())))
        except ValueError:
            pass
    return fallback


def _next_token(payload: dict) -> str | None:
    meta = payload.get("meta") or {}
    token = meta.get("next_token")
    return token if isinstance(token, str) and token else None


def _posts_from_search(payload: dict) -> list[Post]:
    users = {str(user.get("id")): user for user in (payload.get("includes") or {}).get("users") or [] if isinstance(user, dict)}
    posts: list[Post] = []
    for tweet in payload.get("data") or []:
        if not isinstance(tweet, dict):
            continue
        author = users.get(str(tweet.get("author_id")), {})
        metrics = author.get("public_metrics") or {}
        urls = []
        entities = tweet.get("entities") or {}
        for item in entities.get("urls") or []:
            if isinstance(item, dict):
                urls.append(str(item.get("expanded_url") or item.get("url") or ""))
        followers = metrics.get("followers_count")
        username = author.get("username")
        tweet_id = str(tweet.get("id") or "")
        url = f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None
        posts.append(
            Post(
                id=tweet_id or f"api-{len(posts)+1}",
                text=str(tweet.get("text") or ""),
                source="x-api",
                url=url,
                author=str(username) if username else None,
                followers=int(followers) if isinstance(followers, int) else None,
                account_created_at=author.get("created_at") if isinstance(author.get("created_at"), str) else None,
                created_at=tweet.get("created_at") if isinstance(tweet.get("created_at"), str) else None,
                extra_urls=[item for item in urls if item],
            )
        )
    return posts


def _posts_from_user_json(data: object) -> list[Post]:
    rows = data.get("posts") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise SourceError("JSON posting harus berupa daftar atau objek dengan kunci posts")
    posts: list[Post] = []
    for index, row in enumerate(rows, start=1):
        if isinstance(row, str):
            posts.append(Post(id=f"local-{index}", text=row, source="file"))
            continue
        if not isinstance(row, dict):
            continue
        text = str(row.get("text") or "")
        urls = [str(item) for item in row.get("urls") or [] if item]
        if row.get("url"):
            urls.append(str(row["url"]))
        followers = row.get("followers")
        posts.append(
            Post(
                id=str(row.get("id") or f"local-{index}"),
                text=text,
                source="file",
                url=str(row["url"]) if row.get("url") else None,
                author=str(row["author"]) if row.get("author") else None,
                followers=int(followers) if isinstance(followers, int) else None,
                account_created_at=row.get("account_created_at") if isinstance(row.get("account_created_at"), str) else None,
                created_at=row.get("created_at") if isinstance(row.get("created_at"), str) else None,
                extra_urls=urls,
            )
        )
    return posts


def _posts_from_text(raw: str) -> list[Post]:
    chunks = [chunk.strip() for chunk in raw.split("\n\n") if chunk.strip()]
    if not chunks:
        chunks = [raw.strip()] if raw.strip() else []
    return [Post(id=f"local-{index}", text=chunk, source="file") for index, chunk in enumerate(chunks, start=1)]
