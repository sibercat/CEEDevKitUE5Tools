# CEEDevKitUE5Tools

Python tools and migration reference for Conan Exiles mod makers upgrading to UE5.

Run all scripts from the **UE5 Devkit Output Log**:
<p>
  <img src="https://raw.githubusercontent.com/sibercat/CEEDevKitUE5Tools/refs/heads/main/scripts.webp" width="700" height="300" title="hover text">
</p>
---

## Materials

### Why EyeAdaptation → Divide is required in UE5

Conan Exiles UE5 uses **Eye Adaptation** (auto-exposure) which dynamically adjusts scene brightness.
Without compensating for it in emissive materials:

- **Daytime** — emissive glow is barely visible because the scene is bright and eye adaptation dims everything
- **Nighttime** — emissive is massively blown out and overexposed

The fix is to divide the emissive value by the current Eye Adaptation value, so the emissive output
scales correctly with the scene exposure at all times of day.

![EyeAdaptation](https://raw.githubusercontent.com/sibercat/CEEDevKitUE5Tools/refs/heads/main/EyeAdaptationv2.png)


### check_eye_adaptation.py
Scans all Surface materials in your mod folder and reports which ones have Emissive Color connected
but are missing the EyeAdaptation node.

### fix_eye_adaptation.py
Automatically inserts `EyeAdaptation → Divide → Emissive Color` into every material that needs it.

> **⚠️ Backup your mod folder before running this script.**
> It modifies and saves materials automatically with no undo. Make a copy of your Content/Mods folder first.

1. Set `MOD_PATH` to your mod folder
2. Run with `DRY_RUN = True` first to preview changes
3. Set `DRY_RUN = False` to apply

---

## Asset Validation

### check_broken_references.py
Scans **all assets** in your mod folder (Blueprints, particle systems, meshes, materials, etc.) and
reports any references that point to packages that no longer exist.

Useful for finding assets that lost their references during the UE4 → UE5 migration (show as `None` in the editor).
Outputs the old path the reference used to point to, so you can track down or replace the missing asset.

---
### find_devkit_only_refs.py
1. Parses the shipped game's AssetRegistry to build a ground-truth list of what actually exists at runtime
2. Scans every EE asset's dependencies
3. Flags anything that exists in the devkit but is missing from the shipped game — those are your phantom/devkit-only assets causing missing textures.
Run it in the devkit and check devkit_only_refs.txt on your Desktop for the full list.

---
### extract_game_asset_registry.py
It auto-detects common Steam install paths and devkit locations, extracts pakchunk0-Windows.pak using UnrealPak (which handles Oodle automatically), and drops the result in %TEMP%\GameAR\ where find_devkit_only_refs.py expects it.

1. Run extract_game_asset_registry.py once (or after game updates)
2. Run find_devkit_only_refs.py in the devkit to scan for phantom refs
---
## UE4 to UE5 Blueprint API Changes

| UE4 | UE5 | Notes |
|-----|-----|-------|
| `Event StartBuff` | `Event OnStartBuff` | Same pins |
| `Clear Buff` | `Remove Buff Call` (Buff System Interface) | Target = OwningCharacter, pass `Get Class(self)` |
| `Client Clear Buff` | `Remove Buff Call` (Buff System Interface) | Same as above |
| `Remove Buff Widget` | Removed | Widget lifecycle is automatic. Use `OnClearBuff` for cleanup |
| `Add Buff Widget` | `Call Signal Buff Added on Owning Client` | Also needs `Initialize Buff System` first |
| `Get Buff Duration` | `Get Remaining Buff Duration` | Returns remaining seconds (float) |
| `Stop Buff Sound` | `StopBuffSound` | Same node, space removed from name |
| `Get Skeletal Mesh` | `Get Skeletal Mesh Asset` | On SkeletalMeshComponent |
| `CreateInputBox` | `BP_EE_InputBox` subclass pattern | See blueprints/ |
| `ShowInputBox` | `Open(0)` on widget instance | |
| `SignalInputUserActionPerformed` | `OnConfirmed` / `OnCancelled` dispatchers | |

---

## Common Load Errors

### `Invalid value for PACKAGE_FILE_TAG`
UE4 binary asset copied directly into UE5 project. Fix: export as CSV from UE4 devkit, reimport in UE5.

### `Failed import for [Property] ... : [GUID]`
Struct property GUIDs changed between UE4 and UE5. Fix: open the Blueprint, find the Make/Break struct node, right-click Refresh Node.

### `Invalid frame rate provided: -0.001s`
Animation sequence has corrupt frame rate from UE4 to UE5 migration. Fix: enable `Use Default Sample Rate` in Asset Details, or reimport from source FBX.

---
