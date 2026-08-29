from __future__ import annotations

import base64
import hashlib
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
expected = {
    "c1_payload_00.txt": "44c69b72565c4897a3587ba1b6343dd093ece245adf03251d5f6c910c3203ff2",
    "c1_payload_01.txt": "ae7a5cfb14b0f48449212d780c15543ce7e2ea732fe6554d65681966887e4701",
    "c1_payload_02.txt": "2ed42ccab790a0125b78dc016cec22ec7a636197ea01285f21df9899457ae734",
    "c1_payload_03.txt": "bd9b5f36e40173010250fc5b9d9e9ff9da784ac7ada2e961c11576e473ad16ee",
    "c1_payload_04.txt": "6953acacbde48c7412290a4367485f88834e965ec7f390021a1840de1e4981ac",
}
parts = []
for path in sorted((ROOT / "tools").glob("c1_payload_*.txt")):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    print(f"{path.name} size={len(raw)} sha256={digest}")
    if expected.get(path.name) != digest:
        raise RuntimeError(f"payload checksum mismatch: {path.name}")
    parts.append(raw.decode("utf-8"))
payload = "".join(parts)
source = zlib.decompress(base64.b64decode(payload)).decode("utf-8")
exec(compile(source, "tools/implement_tw_c1.py", "exec"))
