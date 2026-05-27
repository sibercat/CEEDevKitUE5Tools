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
import os

# ── Config ────────────────────────────────────────────────────────────────────
MOD_PATH         = "/Game/Mods/ExilesExtreme"
GAME_PKGS_PATH   = r"C:\Users\plane\AppData\Local\Temp\GameAR\game_packages.txt"
OUTPUT_FILE      = r"C:\Users\plane\OneDrive\Desktop\devkit_only_refs.txt"

SKIP_PREFIXES = (
    "/Script/",
    "/Engine/",
    "/Game/Engine/",
    "/Game/Mods/",        # mod assets — ship with EE
    "/Game/ModsShared/",  # shared mod APIs (Pippi, Joshtech etc) — not base game
)

# ── Logging ───────────────────────────────────────────────────────────────────
lines = []
def log(s=""):
    unreal.log(s)
    lines.append(s)

def log_warn(s):
    unreal.log_warning(s)
    lines.append(f"[WARN] {s}")

# ── Load pre-built game package list ─────────────────────────────────────────
def load_game_packages(path):
    """
    Load the text file produced by build_game_package_list.py.
    Each line is a lowercase /Game/ package path from the shipped game.
    """
    game_packages = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    game_packages.add(line)
        log(f"Loaded {len(game_packages)} shipped game package paths")
    except Exception as e:
        log_warn(f"Failed to load game package list: {e}")
        log_warn(f"Run build_game_package_list.py first (plain Python, outside devkit)")
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

if not os.path.exists(GAME_PKGS_PATH):
    log_warn(f"Game package list not found at: {GAME_PKGS_PATH}")
    log_warn("Run build_game_package_list.py first (plain Python 3, outside devkit).")
else:
    game_packages = load_game_packages(GAME_PKGS_PATH)
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
