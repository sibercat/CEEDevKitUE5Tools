"""
extract_game_asset_registry.py

Run this OUTSIDE the devkit — just double-click or run with Python 3.

Extracts AssetRegistry.bin from the shipped Conan Exiles game so that
find_devkit_only_refs.py can compare devkit assets against what actually
exists at runtime.

Requires: UnrealPak.exe from your devkit installation.
"""

import subprocess
import os
import sys
import glob

# ── Auto-detect paths ─────────────────────────────────────────────────────────

STEAM_PATHS = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Conan Exiles",
    r"C:\Program Files\Steam\steamapps\common\Conan Exiles",
    r"D:\SteamLibrary\steamapps\common\Conan Exiles",
    r"D:\Steam\steamapps\common\Conan Exiles",
    r"E:\SteamLibrary\steamapps\common\Conan Exiles",
    r"E:\Steam\steamapps\common\Conan Exiles",
    r"F:\SteamLibrary\steamapps\common\Conan Exiles",
    r"G:\SteamLibrary\steamapps\common\Conan Exiles",
]

DEVKIT_PATHS = [
    r"G:\CEUE5Devkit\Engine\Binaries\Win64\UnrealPak.exe",
    r"F:\CEUE5Devkit\Engine\Binaries\Win64\UnrealPak.exe",
    r"E:\CEUE5Devkit\Engine\Binaries\Win64\UnrealPak.exe",
    r"D:\CEUE5Devkit\Engine\Binaries\Win64\UnrealPak.exe",
    r"C:\CEUE5Devkit\Engine\Binaries\Win64\UnrealPak.exe",
]

OUTPUT_DIR = os.path.join(os.environ.get("TEMP", r"C:\Temp"), "GameAR")


def find_game_path():
    for p in STEAM_PATHS:
        pak = os.path.join(p, "ConanSandbox", "Content", "Paks", "pakchunk0-Windows.pak")
        if os.path.exists(pak):
            return pak
    return None


def find_unrealpak():
    for p in DEVKIT_PATHS:
        if os.path.exists(p):
            return p
    return None


def main():
    print("=" * 60)
    print("Conan Exiles AssetRegistry Extractor")
    print("=" * 60)
    print()

    # ── Find pakchunk0 ────────────────────────────────────────────────────────
    pak_path = find_game_path()
    if not pak_path:
        print("ERROR: Could not find Conan Exiles installation.")
        print("       Edit STEAM_PATHS in this script to add your install path.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    print(f"Found game pak:   {pak_path}")

    # ── Find UnrealPak ────────────────────────────────────────────────────────
    unrealpak = find_unrealpak()
    if not unrealpak:
        print("ERROR: Could not find UnrealPak.exe.")
        print("       Edit DEVKIT_PATHS in this script to add your devkit path.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    print(f"Found UnrealPak:  {unrealpak}")

    # ── Extract ───────────────────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_file = os.path.join(OUTPUT_DIR, "ConanSandbox", "AssetRegistry.bin")

    print(f"Extracting to:    {out_file}")
    print()
    print("Running UnrealPak (Oodle decompression, may take a few seconds)...")

    result = subprocess.run(
        [unrealpak, pak_path, "-Extract", OUTPUT_DIR],
        capture_output=True,
        text=True
    )

    if not os.path.exists(out_file):
        print("ERROR: Extraction failed — AssetRegistry.bin not found after extraction.")
        print("UnrealPak output:")
        print(result.stdout[-2000:] if result.stdout else "(no output)")
        print(result.stderr[-1000:] if result.stderr else "")
        input("\nPress Enter to exit...")
        sys.exit(1)

    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"SUCCESS: Extracted {size_mb:.1f} MB AssetRegistry.bin")
    print()
    print(f"Output: {out_file}")
    print()
    print("You can now run find_devkit_only_refs.py in the devkit.")
    print("=" * 60)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
