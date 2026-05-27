"""
check_broken_references.py

Run from the UE5 devkit Output Log:
  py "C:/Users/plane/OneDrive/Desktop/check_broken_references.py"

Scans all assets under MOD_PATH, finds references that point to
packages that no longer exist, and reports the old path.
"""

import unreal

MOD_PATH = "/Game/Mods/ExilesExtreme"

# Skip these — they are C++ modules or built-in engine content, not broken
SKIP_PREFIXES = (
    "/Script/",
    "/Engine/",
    "/Game/Engine/",
)

def log(msg):      unreal.log(f"[BrokenRefs] {msg}")
def log_warn(msg): unreal.log_warning(f"[BrokenRefs] {msg}")


def package_exists(registry, pkg_name):
    assets = registry.get_assets_by_package_name(pkg_name)
    return len(assets) > 0


def check_broken_references():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()

    ar_filter = unreal.ARFilter(
        package_paths=[MOD_PATH],
        recursive_paths=True
    )
    assets = registry.get_assets(ar_filter)
    log(f"Scanning {len(assets)} assets under {MOD_PATH} ...")

    dep_options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False
    )

    broken_report = {}  # { asset_package : [missing_ref, ...] }

    for asset_data in assets:
        pkg_name = str(asset_data.package_name)

        try:
            deps = registry.get_dependencies(pkg_name, dep_options)
        except Exception as e:
            log_warn(f"Could not get deps for {pkg_name}: {e}")
            continue

        missing = []
        for dep in (deps or []):
            dep_str = str(dep)

            # Skip engine/script packages
            if any(dep_str.startswith(p) for p in SKIP_PREFIXES):
                continue

            if not package_exists(registry, dep_str):
                missing.append(dep_str)

        if missing:
            broken_report[pkg_name] = missing

    # ------------------------------------------------------------------ #
    # Output
    # ------------------------------------------------------------------ #
    log("")
    log("=" * 60)
    log(f"ASSETS WITH BROKEN REFERENCES ({len(broken_report)})")
    log("=" * 60)

    for asset_pkg, missing_refs in sorted(broken_report.items()):
        log(f"\n  ASSET: {asset_pkg}")
        for ref in missing_refs:
            log(f"    MISSING: {ref}")

    log("")
    log("=" * 60)
    log(f"SUMMARY: {len(broken_report)} assets have broken references")
    total_missing = sum(len(v) for v in broken_report.values())
    log(f"         {total_missing} total broken reference(s)")
    log("=" * 60)


check_broken_references()
