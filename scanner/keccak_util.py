"""Keccak-256 kecil untuk selector dan slot EIP-1967.

Tidak ada kunci, tidak ada tanda tangan transaksi. Selector dihitung dari
nama fungsi, jadi repositori tidak perlu menyimpan hash 64-hex.
"""

from __future__ import annotations

_MASK64 = (1 << 64) - 1

# Indeks permutasi rho/pi dari spesifikasi Keccak (bukan hash yang dihitung).
_ROTC = (
    1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 2, 14,
    27, 41, 56, 8, 25, 43, 62, 18, 39, 61, 20, 44,
)
_PILN = (
    10, 7, 11, 17, 18, 3, 5, 16, 8, 21, 24, 4,
    15, 23, 19, 13, 12, 2, 20, 14, 22, 9, 6, 1,
)
_RC = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)


def _rotl(value: int, shift: int) -> int:
    shift %= 64
    if shift == 0:
        return value & _MASK64
    return ((value << shift) | (value >> (64 - shift))) & _MASK64


def _keccak_f(state: list[int]) -> None:
    for round_constant in _RC:
        columns = [
            state[i] ^ state[i + 5] ^ state[i + 10] ^ state[i + 15] ^ state[i + 20]
            for i in range(5)
        ]
        for i in range(5):
            mixed = columns[(i + 4) % 5] ^ _rotl(columns[(i + 1) % 5], 1)
            for row in range(0, 25, 5):
                state[row + i] ^= mixed
        current = state[1]
        for index, target in enumerate(_PILN):
            current, state[target] = state[target], _rotl(current, _ROTC[index])
        for row in range(0, 25, 5):
            lane = state[row : row + 5]
            for i in range(5):
                state[row + i] = (
                    lane[i] ^ ((~lane[(i + 1) % 5]) & lane[(i + 2) % 5])
                ) & _MASK64
        state[0] = (state[0] ^ round_constant) & _MASK64


def keccak256(data: bytes) -> bytes:
    rate = 136
    state = [0] * 25
    pad_len = rate - (len(data) % rate)
    if pad_len == 1:
        padded = data + bytes((0x81,))
    else:
        padded = data + bytes((0x01,)) + bytes(pad_len - 2) + bytes((0x80,))
    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for lane in range(rate // 8):
            state[lane] ^= int.from_bytes(block[lane * 8 : (lane + 1) * 8], "little")
        _keccak_f(state)
    out = bytearray()
    while len(out) < 32:
        for lane in range(rate // 8):
            out += state[lane].to_bytes(8, "little")
            if len(out) >= 32:
                break
        if len(out) < 32:
            _keccak_f(state)
    return bytes(out[:32])


def selector(signature: str) -> bytes:
    """Empat byte pertama Keccak-256 dari tanda fungsi, misalnya mint(uint256)."""
    return keccak256(signature.encode("ascii"))[:4]


def eip1967_slot(label: str) -> bytes:
    """Slot EIP-1967 = keccak256(label) - 1. Labelnya teks, bukan hash tertulis."""
    digest = keccak256(label.encode("ascii"))
    value = int.from_bytes(digest, "big") - 1
    return value.to_bytes(32, "big")
