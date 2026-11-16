#!/usr/bin/env python3
"""Offline invariants for the ImmortalWrt master / Linux 6.18 transition."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fast = (root / ".github/workflows/official-builder.yml").read_text()
full = (root / ".github/workflows/firmware.yml").read_text()
builder = (root / "scripts/official_builder.py").read_text()
verifier = (root / "scripts/verify.py").read_text()
device = (root / "scripts/prepare.py").read_text()

assert fast.count("https://downloads.immortalwrt.org/snapshots/targets/mediatek/filogic") == 2
assert "KFILE=upstream/target/linux/generic/kernel-6.18" in fast
assert 'VERSION="6.18.$PATCH"' in fast
assert "refs/heads/master" in full
assert "--branch master" in full
assert "iwmaster-" in full
assert "immortalwrt-imagebuilder-mediatek-filogic.Linux-x86_64.tar.zst" in builder
assert "ImmortalWrt master SNAPSHOT (official binaries)" in builder
assert '"branch":"master"' in verifier
assert "kmod-mt7915e kmod-mt7981-firmware mt7981-wo-firmware" in device
assert "KERNEL_IN_UBI := 1" in device
assert "UBOOTENV_IN_UBI := 1" in device
assert "25.12-SNAPSHOT" not in fast + builder
assert "openwrt-25.12" not in full
print("ImmortalWrt master 6.18 migration contracts: PASS")
