"""
build_game_package_list.py
Run with plain Python 3 outside the devkit — double-click or:
    python "C:/Users/plane/OneDrive/Desktop/build_game_package_list.py"

Uses UnrealPak -List on every game UTOC to build a complete list of
all package paths that exist in the shipped game.
Output: %TEMP%\GameAR\game_packages.txt  (read by find_devkit_only_refs.py)
"""

import subprocess
import os
import re
import glob

UNREALPAK  = r"G:\CEUE5Devkit\Engine\Binaries\Win64\UnrealPak.exe"
PAKS_DIR   = r"E:\SteamLibrary\steamapps\common\Conan Exiles\ConanSandbox\Content\Paks"
OUT_PATH   = r"C:\Users\plane\AppData\Local\Temp\GameAR\game_packages.txt"

# Pattern: "../../../ConanSandbox/Content/Some/Path/Asset.uasset"
ENTRY_RE = re.compile(r'"\.\.\/\.\.\/\.\.\/(ConanSandbox/Content/[^"]+\.(?:uasset|umap))"')

def utoc_to_packages(utoc_path):
    """Run UnrealPak -List on one UTOC and return set of /Game/ package paths."""
    packages = set()
    try:
        result = subprocess.run(
            [UNREALPAK, utoc_path, "-List"],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout + result.stderr
        for m in ENTRY_RE.finditer(output):
            # ConanSandbox/Content/Characters/Foo/Bar.uasset
            rel = m.group(1)
            # Strip "ConanSandbox/Content/" prefix and file extension
            rel = rel[len("ConanSandbox/Content/"):]
            rel = re.sub(r'\.(uasset|umap)$', '', rel, flags=re.IGNORECASE)
            # Build /Game/ path
            pkg = "/game/" + rel.lower()
            packages.add(pkg)
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {os.path.basename(utoc_path)}")
    except Exception as e:
        print(f"  ERROR on {os.path.basename(utoc_path)}: {e}")
    return packages


def main():
    print("=" * 60)
    print("Conan Exiles Game Package List Builder")
    print("Uses UnrealPak -List on all game UTOCs")
    print("=" * 60)
    print()

    if not os.path.exists(UNREALPAK):
        print(f"ERROR: UnrealPak not found at {UNREALPAK}")
        input("Press Enter to exit...")
        return

    utocs = sorted(glob.glob(os.path.join(PAKS_DIR, "pakchunk*-Windows.utoc")))
    if not utocs:
        print(f"ERROR: No UTOC files found in {PAKS_DIR}")
        input("Press Enter to exit...")
        return

    print(f"Found {len(utocs)} UTOC files to scan")
    print()

    all_packages = set()
    for i, utoc in enumerate(utocs, 1):
        name = os.path.basename(utoc)
        print(f"[{i}/{len(utocs)}] {name} ...", end="", flush=True)
        pkgs = utoc_to_packages(utoc)
        all_packages.update(pkgs)
        print(f" {len(pkgs)} packages ({len(all_packages)} total)")

    print()
    print(f"Total unique game packages: {len(all_packages)}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for p in sorted(all_packages):
            f.write(p + "\n")

    print(f"Saved to: {OUT_PATH}")
    print()
    print("You can now run find_devkit_only_refs.py in the devkit.")
    print("=" * 60)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
