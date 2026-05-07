"""
fix_eye_adaptation.py

Run from the UE5 devkit Output Log:

For every Surface material under MOD_PATH that has Emissive Color connected
but NO EyeAdaptation node, inserts:

  [old emissive node] --> Divide.A
  EyeAdaptation       --> Divide.B
  Divide              --> Emissive Color

Set DRY_RUN = False to apply changes.
"""

import unreal

MOD_PATH = "/Game/Mods/ExilesExtreme"
DRY_RUN  = False

def log(msg):      unreal.log(f"[EyeAdaptFix] {msg}")
def log_warn(msg): unreal.log_warning(f"[EyeAdaptFix] {msg}")


VALID_DOMAINS = {unreal.MaterialDomain.MD_SURFACE}


def has_emissive_connected(mat):
    try:
        node = unreal.MaterialEditingLibrary.get_material_property_input_node(
            mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        return node is not None
    except Exception:
        return False


def has_eye_adaptation_node(mat):
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


def add_eye_adaptation(mat, asset_path):
    try:
        lib = unreal.MaterialEditingLibrary

        # Get the node currently driving Emissive Color
        old_node = lib.get_material_property_input_node(
            mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        if old_node is None:
            log_warn(f"  No emissive node found, skipping: {asset_path}")
            return False

        # Place new nodes to the right of the old emissive node
        try:
            ox = old_node.get_editor_property("material_expression_editor_x")
            oy = old_node.get_editor_property("material_expression_editor_y")
        except Exception:
            ox, oy = -400, 0

        eye_node = lib.create_material_expression(
            mat, unreal.MaterialExpressionEyeAdaptation,
            ox + 350, oy + 150
        )
        div_node = lib.create_material_expression(
            mat, unreal.MaterialExpressionDivide,
            ox + 350, oy
        )

        # old emissive â†’ Divide A
        lib.connect_material_expressions(old_node, "", div_node, "A")

        # EyeAdaptation â†’ Divide B
        lib.connect_material_expressions(eye_node, "", div_node, "B")

        # Divide â†’ Emissive Color
        lib.connect_material_property(
            div_node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )

        lib.recompile_material(mat)

        unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=True)
        return True

    except Exception as e:
        log_warn(f"  FAILED {asset_path}: {e}")
        return False


def fix_materials():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    ar_filter = unreal.ARFilter(
        class_names=["Material"],
        package_paths=[MOD_PATH],
        recursive_paths=True
    )
    assets = registry.get_assets(ar_filter)

    log(f"Scanning {len(assets)} materials under {MOD_PATH} ...")
    if DRY_RUN:
        log("*** DRY RUN â€” no changes will be made. Set DRY_RUN = False to apply. ***")

    would_fix = []
    fixed     = []
    already   = []
    failed    = []

    for asset_data in assets:
        asset_path = f"{asset_data.package_name}.{asset_data.asset_name}"
        mat = unreal.load_asset(asset_path)

        if not mat or not isinstance(mat, unreal.Material):
            continue

        try:
            if mat.get_editor_property("material_domain") not in VALID_DOMAINS:
                continue
        except Exception:
            pass

        if not has_emissive_connected(mat):
            continue

        if has_eye_adaptation_node(mat):
            already.append(asset_path)
            continue

        if DRY_RUN:
            log(f"  WOULD FIX: {asset_path}")
            would_fix.append(asset_path)
        else:
            log(f"  Fixing: {asset_path}")
            if add_eye_adaptation(mat, asset_path):
                log(f"    OK")
                fixed.append(asset_path)
            else:
                failed.append(asset_path)

    log("")
    log("=" * 60)
    log("SUMMARY")
    if DRY_RUN:
        log(f"  Would fix      : {len(would_fix)}")
        log(f"  Already fixed  : {len(already)}")
        log("")
        log("  Set DRY_RUN = False to apply changes.")
    else:
        log(f"  Fixed          : {len(fixed)}")
        log(f"  Already fixed  : {len(already)}")
        log(f"  Failed         : {len(failed)}")
        for f in failed:
            log_warn(f"    FAIL: {f}")
    log("=" * 60)


fix_materials()
