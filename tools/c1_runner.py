from __future__ import annotations

import base64
import hashlib
import os
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


def replace_exact(path: str, old: str, new: str, expected_count: int) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    actual = text.count(old)
    if actual != expected_count:
        raise RuntimeError(
            f"{path}: expected {expected_count} occurrences of {old!r}, found {actual}"
        )
    target.write_text(text.replace(old, new), encoding="utf-8")


# Keep the source root at exactly ten latest observation JSON files for backward
# compatibility; the mutable catalog lives below status/ while Pages still
# publishes it at /data/observations/catalog.json.
replace_exact(
    "src/ingestion/twse_archive.py",
    'observation_dir / "catalog.json"',
    'observation_dir / "status" / "catalog.json"',
    3,
)
replace_exact(
    "tests/unit/test_twse_archive.py",
    'root / "catalog.json"',
    'root / "status" / "catalog.json"',
    2,
)
replace_exact(
    "src/render/site.py",
    '<span>官方觀測納入模型</span>',
    '<span>官方觀測納入模型：0</span>',
    1,
)
replace_exact(
    "README.md",
    '`catalog.json` 維護 latest、last-known-good、history count、official as-of、資料新鮮度與 model-input coverage。',
    '`data/observations/twse/status/catalog.json` 維護 latest、last-known-good、history count、official as-of、資料新鮮度與 model-input coverage。',
    1,
)
source_catalog = ROOT / "data" / "observations" / "twse" / "catalog.json"
target_catalog = ROOT / "data" / "observations" / "twse" / "status" / "catalog.json"
target_catalog.parent.mkdir(parents=True, exist_ok=True)
os.replace(source_catalog, target_catalog)
print("TW-C1 compatibility fixes applied")
