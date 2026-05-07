"""
Scans all Materials under MOD_PATH:
  - Skips materials with no Emissive Color connected
  - Reports materials that have Emissive but NO EyeAdaptation node  (needs fix)
  - Reports materials that already have an EyeAdaptation node        (already fixed)
"""

import unreal

MOD_PATH = "/Game/Mods/ExilesExtreme"

def log(msg):      unreal.log(f"[EyeAdaptCheck] {msg}")
def log_warn(msg): unreal.log_warning(f"[EyeAdaptCheck] {msg}")


def has_emissive_connected(mat):
    try:
        node = unreal.MaterialEditingLibrary.get_material_property_input_node(
            mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        return node is not None
    except Exception:
        return False


def has_eye_adaptation_node(mat):
    """
    Use ObjectIterator to find MaterialExpressionEyeAdaptation nodes
    whose outer is this material. This avoids the protected expressions array.
    """
    try:
        for expr in unreal.ObjectIterator(unreal.MaterialExpressionEyeAdaptation):
            try:
                if expr.get_outer() == mat:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def check_materials():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()

    ar_filter = unreal.ARFilter(
        class_names=["Material"],
        package_paths=[MOD_PATH],
        recursive_paths=True
    )

    assets = registry.get_assets(ar_filter)
    log(f"Scanning {len(assets)} materials under {MOD_PATH} ...")

    needs_fix     = []
    already_fixed = []
    no_emissive   = 0
    skipped_domain = 0

    # Only Surface materials in the 3D world need EyeAdaptation
    VALID_DOMAINS = {
        unreal.MaterialDomain.MD_SURFACE,
    }

    for asset_data in assets:
        asset_path = f"{asset_data.package_name}.{asset_data.asset_name}"
        mat = unreal.load_asset(asset_path)

        if not mat or not isinstance(mat, unreal.Material):
            continue

        # Skip UI, Post Process, Decal, Volume, etc.
        try:
            domain = mat.get_editor_property("material_domain")
            if domain not in VALID_DOMAINS:
                skipped_domain += 1
                continue
        except Exception:
            pass

        if not has_emissive_connected(mat):
            no_emissive += 1
            continue

        if has_eye_adaptation_node(mat):
            already_fixed.append(asset_path)
        else:
            needs_fix.append(asset_path)

    # ------------------------------------------------------------------ #
    # Output
    # ------------------------------------------------------------------ #
    log("")
    log("=" * 60)
    log(f"NEEDS EYE ADAPTATION NODE ({len(needs_fix)} materials)")
    log("=" * 60)
    for m in needs_fix:
        log(f"  NEEDS FIX: {m}")

    log("")
    log("=" * 60)
    log(f"ALREADY FIXED ({len(already_fixed)} materials)")
    log("=" * 60)
    for m in already_fixed:
        log(f"  OK: {m}")

    log("")
    log("=" * 60)
    log(f"SUMMARY")
    log(f"  Needs fix    : {len(needs_fix)}")
    log(f"  Already fixed: {len(already_fixed)}")
    log(f"  No emissive  : {no_emissive}  (skipped)")
    log(f"  Non-surface  : {skipped_domain}  (skipped â€” UI/Decal/PostProcess/etc)")
    log("=" * 60)


check_materials()
