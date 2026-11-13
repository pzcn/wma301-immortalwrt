#!/usr/bin/env python3
"""Offline verification for official-ImageBuilder sysupgrade-only output.

Do not pretend that ImageBuilder built a recovery/initramfs FIT. The existing
full-source scripts/verify.py remains the authority for its two FIT outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from verify import verify_one

NAME_RE = re.compile(r".*tplink_wma301-v2-squashfs-sysupgrade\.itb$")


def verify_fast(images: Path, output: Path, provenance: Path, local_sha: str) -> dict:
    candidates = sorted(p for p in images.iterdir()
                        if p.is_file() and NAME_RE.fullmatch(p.name))
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one WMA301 sysupgrade FIT, found {len(candidates)}")
    source = json.loads(provenance.read_text())
    if source.get("target") != "mediatek/filogic":
        raise ValueError("wrong official ImageBuilder target")
    if not re.fullmatch(r"[0-9a-f]{40}", local_sha):
        raise ValueError("invalid local commit")
    report = verify_one(candidates[0], persistent=True)
    output.mkdir(parents=True, exist_ok=True)
    target = output / candidates[0].name
    target.write_bytes(candidates[0].read_bytes())
    manifest = {
        "build": "official-imagebuilder-fast",
        "device": "tplink,wma301-v2",
        "recovery": "NOT_BUILT_USE_FULL_SOURCE_WORKFLOW",
        "hardware_validation": "NOT_TESTED",
        "builder": source,
        "local_sha": local_sha,
        "output": report,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "SHA256SUMS").write_text(
        f"{hashlib.sha256(target.read_bytes()).hexdigest()}  {target.name}\n"
    )
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--images", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--provenance", type=Path, required=True)
    p.add_argument("--local-sha", required=True)
    args = p.parse_args()
    print(json.dumps(verify_fast(args.images, args.output, args.provenance,
                                args.local_sha), indent=2))
