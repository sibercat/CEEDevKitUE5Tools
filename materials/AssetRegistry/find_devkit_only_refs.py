"""
find_devkit_only_refs.py

Run inside the UE5 devkit Python console:
    File → Execute Python Script → select this file

Finds EE assets that reference base-game packages which exist in the
devkit but NOT in the shipped game (devkit-only / phantom assets).

These cause missing textures / missing materials at runtime even though
everything looks fine inside the devkit editor.

Reads the shipped game's AssetRegistry.bin to build a ground-truth set
of what actually exists at runtime.
"""

import unreal
import struct
import os

# ── Config ────────────────────────────────────────────────────────────────────
MOD_PATH        = "/Game/Mods/ExilesExtreme"
GAME_AR_PATH    = r"C:\Users\plane\AppData\Local\Temp\GameAR\ConanSandbox\AssetRegistry.bin"
OUTPUT_FILE     = r"C:\Users\plane\OneDrive\Desktop\devkit_only_refs.txt"

SKIP_PREFIXES = (
    "/Script/",
    "/Engine/",
    "/Game/Engine/",
    "/Game/Mods/",      # mod assets are fine — they ship with EE
)

# ── Logging ───────────────────────────────────────────────────────────────────
lines = []
def log(s=""):
    unreal.log(s)
    lines.append(s)

def log_warn(s):
    unreal.log_warning(s)
    lines.append(f"[WARN] {s}")

# ── Parse shipped game AssetRegistry ─────────────────────────────────────────
def read_game_asset_registry(path):
    """
    Parse the shipped AssetRegistry.bin and return a set of lowercase
    package names that exist in the shipped game.

    Format (UE5):
      4 bytes  magic  0x717F9EE7
      4 bytes  version
      name table: 4-byte count, then N length-prefixed strings
      asset records follow (we only need the name table for package paths
      since all referenced package names appear in it)
    """
    game_packages = set()

    try:
        with open(path, "rb") as f:
            data = f.read()

        offset = 0

        def read_u32():
            nonlocal offset
            v = struct.unpack_from("<I", data, offset)[0]
            offset += 4
            return v

        def read_str():
            nonlocal offset
            length = struct.unpack_from("<i", data, offset)[0]
            offset += 4
            if length == 0:
                return ""
            if length > 0:
                raw = data[offset:offset+length]
                offset += length
                return raw.decode("utf-8", errors="replace").rstrip("\x00")
            else:
                # UTF-16 LE (negative length in UE)
                byte_len = (-length) * 2
                raw = data[offset:offset+byte_len]
                offset += byte_len
                return raw.decode("utf-16-le", errors="replace").rstrip("\x00")

        magic = read_u32()
        if magic != 0x717F9EE7:
            log_warn(f"AssetRegistry magic mismatch: 0x{magic:08X} (expected 0x717F9EE7)")
            log_warn("Attempting to parse anyway...")

        version = read_u32()
        log(f"Game AssetRegistry version: {version}")

        name_count = read_u32()
        log(f"Game AssetRegistry name table: {name_count} entries")

        for _ in range(name_count):
            name = read_str()
            # Package paths start with /Game/ or /Engine/
            if name.startswith("/Game/") or name.startswith("/Engine/"):
                game_packages.add(name.lower())

        log(f"Loaded {len(game_packages)} /Game/ + /Engine/ paths from shipped AssetRegistry")

    except Exception as e:
        log_warn(f"Failed to parse game AssetRegistry: {e}")
        log_warn("Check that the file was extracted correctly.")

    return game_packages


# ── Main scan ─────────────────────────────────────────────────────────────────
def find_devkit_only_refs(game_packages):
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()

    ar_filter = unreal.ARFilter(
        package_paths=[MOD_PATH],
        recursive_paths=True
    )
    assets = registry.get_assets(ar_filter)
    log(f"Scanning {len(assets)} EE assets ...")

    dep_options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False
    )

    phantom_report = {}  # { ee_asset : [devkit_only_dep, ...] }

    for asset_data in assets:
        pkg_name = str(asset_data.package_name)

        try:
            deps = registry.get_dependencies(pkg_name, dep_options)
        except Exception:
            continue

        phantoms = []
        for dep in (deps or []):
            dep_str = str(dep)

            # Skip known-safe prefixes
            if any(dep_str.startswith(p) for p in SKIP_PREFIXES):
                continue

            # Only check /Game/ base game refs (not EE's own assets)
            if not dep_str.startswith("/Game/"):
                continue

            # If it's in the devkit registry but NOT in the shipped game → phantom
            devkit_exists = len(registry.get_assets_by_package_name(dep_str)) > 0
            if devkit_exists and dep_str.lower() not in game_packages:
                phantoms.append(dep_str)

        if phantoms:
            phantom_report[pkg_name] = phantoms

    return phantom_report


# ── Run ───────────────────────────────────────────────────────────────────────
log("=" * 70)
log("Devkit-Only Reference Finder")
log("Finds base-game assets that exist in devkit but NOT in shipped game")
log("=" * 70)
log()

if not os.path.exists(GAME_AR_PATH):
    log_warn(f"Game AssetRegistry not found at: {GAME_AR_PATH}")
    log_warn("Run extraction step first (see instructions).")
else:
    game_packages = read_game_asset_registry(GAME_AR_PATH)
    log()

    if game_packages:
        phantom_report = find_devkit_only_refs(game_packages)

        log()
        log("=" * 70)
        log(f"DEVKIT-ONLY REFERENCES ({len(phantom_report)} EE assets affected)")
        log("=" * 70)

        for ee_pkg, phantoms in sorted(phantom_report.items()):
            log()
            log(f"  EE ASSET: {ee_pkg}")
            for p in phantoms:
                log(f"    PHANTOM: {p}")

        log()
        log("=" * 70)
        log("SUMMARY")
        log("=" * 70)
        total = sum(len(v) for v in phantom_report.values())
        log(f"  {len(phantom_report)} EE assets reference devkit-only base-game packages")
        log(f"  {total} total phantom references")
        log()
        log("HOW TO FIX EACH:")
        log("  1. Open the EE asset in the devkit editor")
        log("  2. Find references to the PHANTOM path (check material slots,")
        log("     texture parameters, mesh references, Blueprint variables)")
        log("  3. Replace with a valid shipped asset OR use a fallback default")
        log("     (e.g. Engine default material, your own EE texture)")
        log("  4. Compile & Save, then re-cook")

# Save
try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    unreal.log(f"Saved to: {OUTPUT_FILE}")
except Exception as e:
    unreal.log_warning(f"Could not save: {e}")

log("=" * 70)
log("DONE")
log("=" * 70)
