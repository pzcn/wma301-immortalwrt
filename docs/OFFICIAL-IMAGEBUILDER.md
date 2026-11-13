# WMA301 official ImageBuilder fast-path

The experimental workflow [official-builder.yml](../.github/workflows/official-builder.yml)
reuses upstream **ImmortalWrt 25.12-SNAPSHOT / mediatek/filogic** binaries.
The original [firmware.yml](../.github/workflows/firmware.yml) remains an
independent full-source build fallback and still produces both recovery and
sysupgrade FIT images.

## What is reused

* The official Linux Image, kernel ABI, kernel modules, base packages and LuCI.
* The official ImageBuilder's FIT generation, filesystem tools and APK package repositories.
* The official source's board.d, sysupgrade and U-Boot environment utilities,
  with WMA301 board cases added using our existing source integration.

The fast-path compiles **only the WMA301 DTB**, and compresses the **existing**
official kernel Image; it does not rebuild Linux or third-party APK packages.

## Reproducibility and source identity

The workflow reads `version.buildinfo` and `sha256sums` from the same official
filogic output directory, verifies the ImageBuilder tarball SHA256, and resolves
the version's short Git revision to a **full upstream commit SHA**. The matching
upstream source is checked out at that exact SHA; its device-specific shell
files are staged into a FILES overlay, while the original source tree and
upstream firmware are left untouched.

The official kernel's `include/dt-bindings` headers are obtained from
kernel.org using the **exact kernel tarball SHA256 specified by upstream**
`target/linux/generic/kernel-6.12`. The ImageBuilder supplies the matching
already-compiled kernel Image, kernel DT sources and dtc.

Do not substitute a newer SDK, kernel, kmod feed, or HEAD checkout for the
chosen official Builder. Official snapshots may lag upstream Git HEAD. If
the released binaries cannot be matched to a source revision, fail instead
of silently compiling against an unrelated source.

## Build and artifacts

1. Run the **WMA301 | Official ImageBuilder fast-path (experimental)** workflow.
2. Offline tests run before downloading the approximately 1 GiB Builder.
3. The workflow adds the WMA301 profile, local DTS, and WMA301 runtime hooks.
4. `make image PROFILE=tplink_wma301-v2 PACKAGES=luci FILES=...` builds the
   persistent `squashfs-sysupgrade.itb`.
5. `verify_official.py` runs the same FIT hash, image contents and NAND/DTS
   checks as `verify.py`.

The workflow uploads only a short-lived GitHub Actions artifact, **not a
Release**. The existing full-source releases are not replaced or modified.

## Important limitations

* Official ImageBuilder does **not** compile device initramfs recovery images.
  Use the full-source build for `initramfs-recovery.itb`.
* This phase uses the official packages and only adds the `luci` package.
  Third-party SDK APK compilation is intentionally not wired into the workflow
  yet. The official matching SDK name/SHA is recorded in provenance metadata.
* This is **offline validation only**. Power-cycle persistence, actual flash
  reliability at 52 MHz, UBI environment retention, Ethernet, MAC addresses,
  Wi-Fi and device recovery still require hardware testing.
* The WMA301 FIT is **not** an OEM A/B stock firmware or `ubiformat` input.
  It is intended only for devices with the already-migrated single-UBI layout.
* If an upstream ImageBuilder lacks required kernel DT sources, kernel Image,
  matching source revision, or compatible FIT build recipes, the fast build
  fails explicitly. Run the old full-source workflow instead.

For standalone source tests run:

```sh
python3 scripts/test_official_builder.py
python3 scripts/test_layout.py
```
