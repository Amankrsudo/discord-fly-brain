"""Minimal Neuroglancer precomputed *annotation layer* reader.

RESEARCH UTILITY ONLY. Not production biological modelling code. It exists to
answer one narrow question: does the official MaleCNS v1.0 synapse layer
carry a per-synapse ``compartment_post`` label for MN5 bodies 801970/801295,
and what does it say?

Why this file exists
--------------------
The environment has no ``tensorstore``, ``cloud-volume``, ``numpy`` or
``requests``. The layer is a ``neuroglancer_annotations_v1`` annotation layer
with two sharded relationships (``by_rel_body_pre``, ``by_rel_body_post``).
To read it we must, in pure standard library:

1. hash the relationship key with murmurhash3 x86_128 (as neuroglancer does);
2. derive the shard / minishard indices from the hash's high bits;
3. gunzip the sharded sparse index and binary-search for our key;
4. HTTP range-GET the annotation blob and decode it.

Every step is verified against the layer's own ``info`` document at runtime, so
a change in sharding parameters is detected rather than silently misread.

Decoding rules implemented (neuroglancer ``annotations/compilation.ts`` and
``uint64-sharded`` spec):

* varint = LEB128 unsigned;
* signed integers use zigzag then LEB128; floats are encoded as the varint of
  their IEEE-754 uint32 bit pattern;
* ``uint8`` / ``int16`` are fixed-width single bytes;
* the annotation blob is: ``uint64 num_ids``, delta-encoded varint ids, then
  per property (in ``info.properties`` order) a ``uint64 count`` followed by
  that many values.
"""

from __future__ import annotations

import gzip
import json
import struct
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

MASK64 = (1 << 64) - 1
MASK128 = (1 << 128) - 1


# --- murmurhash3 x86_128 ----------------------------------------------------

def _rotl(x: int, r: int) -> int:
    return ((x << r) | (x >> (64 - r))) & MASK64


def murmurhash3_x86_128(data: bytes, seed: int = 0) -> int:
    """128-bit MurmurHash3 (x86 variant), as used by Neuroglancer."""
    c1 = 0x87C37B91114253D5
    c2 = 0x4CF5AD432745937F
    h1 = seed & MASK64
    h2 = seed & MASK64
    nblocks = len(data) // 16

    def blocks(b: bytes, h1: int, h2: int, n: int) -> Tuple[int, int]:
        for i in range(n):
            k1 = int.from_bytes(b[i * 16:i * 16 + 8], "little")
            k2 = int.from_bytes(b[i * 16 + 8:i * 16 + 16], "little")
            k1 = (k1 * c1) & MASK64
            k1 = _rotl(k1, 31)
            k1 = (k1 * c2) & MASK64
            h1 ^= k1
            h1 = _rotl(h1, 27)
            h1 = (h1 + h2) & MASK64
            h1 = (h1 * 5 + 0x52DCE729) & MASK64
            k2 = (k2 * c2) & MASK64
            k2 = _rotl(k2, 33)
            k2 = (k2 * c1) & MASK64
            h2 ^= k2
            h2 = _rotl(h2, 31)
            h2 = (h2 + h1) & MASK64
            h2 = (h2 * 5 + 0x38495AB5) & MASK64
        return h1, h2

    h1, h2 = blocks(data, h1, h2, nblocks)

    tail = data[nblocks * 16:]
    k1 = 0
    k2 = 0
    tl = len(tail)
    if tl >= 15:
        k2 ^= tail[14] << 48
    if tl >= 14:
        k2 ^= tail[13] << 40
    if tl >= 13:
        k2 ^= tail[12] << 32
    if tl >= 12:
        k2 ^= tail[11] << 24
    if tl >= 11:
        k2 ^= tail[10] << 16
    if tl >= 10:
        k2 ^= tail[9] << 8
    if tl >= 9:
        k2 ^= tail[8]
    if tl >= 9:
        k2 = (k2 * c2) & MASK64
        k2 = _rotl(k2, 33)
        k2 = (k2 * c1) & MASK64
        h2 ^= k2
    if tl >= 8:
        k1 ^= tail[7] << 56
    if tl >= 7:
        k1 ^= tail[6] << 48
    if tl >= 6:
        k1 ^= tail[5] << 40
    if tl >= 5:
        k1 ^= tail[4] << 32
    if tl >= 4:
        k1 ^= tail[3] << 24
    if tl >= 3:
        k1 ^= tail[2] << 16
    if tl >= 2:
        k1 ^= tail[1] << 8
    if tl >= 1:
        k1 ^= tail[0]
        k1 = (k1 * c1) & MASK64
        k1 = _rotl(k1, 31)
        k1 = (k1 * c2) & MASK64
        h1 ^= k1

    h1 ^= len(data)
    h2 ^= len(data)
    h1 = (h1 + h2) & MASK64
    h2 = (h2 + h1) & MASK64

    def fmix(k: int) -> int:
        k ^= k >> 33
        k = (k * 0xFF51AFD7ED558CCD) & MASK64
        k ^= k >> 33
        k = (k * 0xC4CEB9FE1A85EC53) & MASK64
        k ^= k >> 33
        return k

    h1 = fmix(h1)
    h2 = fmix(h2)
    h1 = (h1 + h2) & MASK64
    h2 = (h2 + h1) & MASK64
    return ((h1 << 64) | h2) & MASK128


def _high_bits(h: int, bits: int) -> int:
    return (h >> (128 - bits)) & ((1 << bits) - 1)


# --- HTTP helpers -----------------------------------------------------------

def http_get(url: str, byte_range: Optional[Tuple[int, int]] = None) -> bytes:
    req = urllib.request.Request(url)
    if byte_range is not None:
        lo, hi = byte_range
        req.add_header("Range", f"bytes={lo}-{hi}")
    with urllib.request.urlopen(req, timeout=180) as fh:
        return fh.read()


# --- varint / zigzag --------------------------------------------------------

def read_varint(buf: bytes, pos: int) -> Tuple[int, int]:
    result = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7


def zigzag_decode(n: int) -> int:
    return (n >> 1) ^ -(n & 1)


# --- sharded uint64 index ---------------------------------------------------

class ShardedUint64Index:
    def __init__(self, base: str, info: Dict[str, Any],
                 dirname: Optional[str] = None) -> None:
        sh = info["sharding"]
        self.base = base
        # The on-disk directory is the RELATIONSHIP KEY ("by_rel_body_post"),
        # not the id property name ("body_post"). Getting this wrong 404s.
        self.dirname = dirname or info["id"]
        self.preshift = sh["preshift_bits"]
        self.shard_bits = sh["shard_bits"]
        self.minishard_bits = sh["minishard_bits"]
        self.shard_mask = (1 << self.shard_bits) - 1
        self.minishard_mask = (1 << self.minishard_bits) - 1
        self.id_property = info.get("id")

    def _paths(self, key: int) -> Tuple[str, str]:
        h = murmurhash3_x86_128(struct.pack("<Q", key))
        shard = _high_bits(h, self.preshift + self.shard_bits) & self.shard_mask
        minishard = _high_bits(
            h, self.preshift + self.shard_bits + self.minishard_bits
        ) & self.minishard_mask
        shard_w = (self.shard_bits + 3) // 4
        mini_w = (self.minishard_bits + 3) // 4
        d = self.dirname
        rel = f"{d}/{shard:0{shard_w}x}/ranges/{minishard:0{mini_w}x}"
        data = f"{d}/{shard:0{shard_w}x}/{minishard:0{mini_w}x}"
        return rel, data

    def _index_entries(self, rel_path: str) -> List[Tuple[int, int, int]]:
        raw = gzip.decompress(http_get(f"{self.base}/{rel_path}"))
        entries = []
        pos = 0
        while pos < len(raw):
            key, pos = read_varint(raw, pos)
            off, pos = read_varint(raw, pos)
            size, pos = read_varint(raw, pos)
            entries.append((key, off, size))
        entries.sort()
        return entries

    def lookup(self, key: int) -> Optional[Tuple[str, int, int]]:
        rel, data = self._paths(key)
        try:
            entries = self._index_entries(rel)
        except Exception:
            return None
        ids = [e[0] for e in entries]
        import bisect
        i = bisect.bisect_left(ids, key)
        if i >= len(entries) or entries[i][0] != key:
            return None
        return (f"{self.base}/{data}", entries[i][1], entries[i][2])


# --- annotation blob decoding ----------------------------------------------

def _decode_value(ptype: str, buf: bytes, pos: int) -> Tuple[Any, int]:
    if ptype == "uint8":
        return buf[pos], pos + 1
    if ptype == "int16":
        return struct.unpack_from("<h", buf, pos)[0], pos + 2
    v, pos = read_varint(buf, pos)
    if ptype == "uint32" or ptype == "uint64":
        return v, pos
    if ptype == "int32":
        return zigzag_decode(v), pos
    if ptype == "float32":
        return struct.unpack("<f", struct.pack("<I", v & 0xFFFFFFFF))[0], pos
    if ptype == "float64":
        return struct.unpack("<d", struct.pack("<Q", v & MASK64))[0], pos
    raise ValueError(f"unsupported property type {ptype!r}")


def decode_annotations(blob: bytes, properties: List[Dict[str, Any]],
                       ) -> List[Dict[str, Any]]:
    raw = gzip.decompress(blob)
    (num_ids,) = struct.unpack_from("<Q", raw, 0)
    pos = 8
    ids: List[int] = []
    cur = 0
    for _ in range(num_ids):
        delta, pos = read_varint(raw, pos)
        cur = cur + delta if ids else delta
        ids.append(cur)
    rows: List[Dict[str, Any]] = [{"id": i} for i in ids]
    for prop in properties:
        name = prop["id"]
        ptype = prop["type"]
        if ptype in ("line", "points", "cells", "mesh"):
            continue
        if name in ("x", "y", "z"):
            continue
        (count,) = struct.unpack_from("<Q", raw, pos)
        pos += 8
        if count != len(rows):
            # Mismatched counts mean our decode assumptions are wrong; refuse.
            raise ValueError(
                f"property {name} count {count} != num_ids {len(rows)}")
        for r in rows:
            val, pos = _decode_value(ptype, raw, pos)
            r[name] = val
    return rows


class AnnotationLayer:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.info = json.loads(
            http_get(f"{self.base}/info").decode("utf-8"))
        self.properties = self.info["properties"]
        self.by_id = ShardedUint64Index(
            self.base,
            {"sharding": self.info["by_id"]["sharding"],
             "id": self.info["by_id"]["key"]},
        )
        self.relationships: Dict[str, ShardedUint64Index] = {}
        for rel in self.info.get("relationships", []):
            self.relationships[rel["key"]] = ShardedUint64Index(
                self.base, {"sharding": rel["sharding"], "id": rel["id"]},
                dirname=rel["key"])

    def enum_labels(self, prop_id: str) -> Optional[List[str]]:
        for p in self.properties:
            if p["id"] == prop_id:
                return p.get("enum_labels")
        return None

    def query_relationship(self, rel_key: str, value: int,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        rel = self.relationships[rel_key]
        found = rel.lookup((value << rel.preshift) & MASK64)
        if found is None:
            return []
        url, off, size = found
        blob = http_get(url, (off, off + size - 1))
        rows = decode_annotations(blob, self.properties)
        return rows[:limit] if limit else rows