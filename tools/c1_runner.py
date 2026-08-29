from __future__ import annotations

import base64
import hashlib
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
expected = {
    "c1_payload_00_00.txt": "35063bfa1a257536412bfcd3d0897f3f7eff95f71f49bbf205ca094fc3ca79d1",
    "c1_payload_00_01.txt": "d38da9e6694da2f404aa8776a553003ce6f534fdcf86a4baa05c8bfc40f61dfe",
    "c1_payload_00_02.txt": "45320bcd6996afeab3d31fb0294363c226968d428db701c062fb020fa5aeb221",
    "c1_payload_00_03.txt": "77ca09e9dfed0f50bd20166a9b42ac103234abd79ab0b549a467256469692ac6",
    "c1_payload_00_04.txt": "9e86c91c41000f0349e3e66acf8e40cf9db21fe67f4d4dcd30b02a4d4c2a1841",
    "c1_payload_01.txt": "ae7a5cfb14b0f48449212d780c15543ce7e2ea732fe6554d65681966887e4701",
    "c1_payload_02.txt": "2ed42ccab790a0125b78dc016cec22ec7a636197ea01285f21df9899457ae734",
    "c1_payload_03.txt": "bd9b5f36e40173010250fc5b9d9e9ff9da784ac7ada2e961c11576e473ad16ee",
    "c1_payload_04.txt": "6953acacbde48c7412290a4367485f88834e965ec7f390021a1840de1e4981ac",
}
parts = []
paths = sorted((ROOT / "tools").glob("c1_payload_*.txt"))
if {path.name for path in paths} != set(expected):
    raise RuntimeError("payload file set mismatch")
for path in paths:
    raw = path.read_text(encoding="utf-8").strip().encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    print(f"{path.name} size={len(raw)} sha256={digest}")
    if expected[path.name] != digest:
        raise RuntimeError(f"payload checksum mismatch: {path.name}")
    parts.append(raw.decode("utf-8"))
payload = "".join(parts)
source = zlib.decompress(base64.b64decode(payload)).decode("utf-8")
exec(compile(source, "tools/implement_tw_c1.py", "exec"))
