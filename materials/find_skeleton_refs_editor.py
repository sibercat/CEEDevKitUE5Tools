"""
find_skeleton_refs_editor.py

Run from the UE5 devkit Output Log:
  py "C:/Users/plane/OneDrive/Desktop/find_skeleton_refs_editor.py"

Scans all assets under MOD_PATH and finds every asset that has
sk_human_skeleton (or any SEARCH_TARGET you set) as a dependency.
Results are printed to the Output Log and saved to OUTPUT_FILE.
"""

import unreal

MOD_PATH      = "/Game/Mods/ExilesExtreme"
SEARCH_TARGET = "/Game/Characters/humans/meshes/sk_human_skeleton"
OUTPUT_FILE   = r"C:\Users\MyPC\OneDrive\Desktop\sk_human_skeleton_refs.txt"

SKIP_PREFIXES = (
    "/Script/",
    "/Engine/",
    "/Game/Engine/",
)

def log(msg):      unreal.log(f"[SkeletonRefs] {msg}")
def log_warn(msg): unreal.log_warning(f"[SkeletonRefs] {msg}")


def find_skeleton_refs():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()

    ar_filter = unreal.ARFilter(
        package_paths=[MOD_PATH],
        recursive_paths=True
    )
    assets = registry.get_assets(ar_filter)
    log(f"Scanning {len(assets)} assets under {MOD_PATH} ...")
    log(f"Looking for references to: {SEARCH_TARGET}")

    dep_options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False
    )

    found = []

    for asset_data in assets:
        pkg_name = str(asset_data.package_name)

        try:
            deps = registry.get_dependencies(pkg_name, dep_options)
        except Exception as e:
            log_warn(f"Could not get deps for {pkg_name}: {e}")
            continue

        for dep in deps:
            dep_str = str(dep)
            if any(dep_str.startswith(p) for p in SKIP_PREFIXES):
                continue
            if SEARCH_TARGET.lower() in dep_str.lower():
                found.append((pkg_name, dep_str))
                break  # one match per asset is enough

    # ------------------------------------------------------------------ #
    # Output
    # ------------------------------------------------------------------ #
    log("")
    log("=" * 60)
    log(f"ASSETS REFERENCING {SEARCH_TARGET}")
    log("=" * 60)

    for asset_pkg, dep_str in sorted(found):
        log(f"  {asset_pkg}")

    log("")
    log(f"TOTAL: {len(found)} asset(s) reference this skeleton")
    log("=" * 60)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Assets referencing: {SEARCH_TARGET}\n\n")
        for asset_pkg, dep_str in sorted(found):
            f.write(asset_pkg + "\n")

    log(f"Saved to: {OUTPUT_FILE}")


find_skeleton_refs()
