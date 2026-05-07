# CEEDevKitUE5Tools

Python tools and migration reference for Conan Exiles mod makers upgrading to UE5.

Run all scripts from the **UE5 Devkit Output Log**:


---

## Materials

### check_eye_adaptation.py
Scans all Surface materials in your mod folder and reports which ones have Emissive Color connected but are missing the required EyeAdaptation node.

**UE5 requires EyeAdaptation → Divide on all emissive materials to prevent blown-out brightness.**

### fix_eye_adaptation.py
Automatically inserts  into every material that needs it.

1. Set  to your mod folder
2. Run with  first to preview changes
3. Set  to apply

---

## Blueprints

### create_bp_ee_inputbox.py
Creates  as a subclass of .

Required because UE5 removed , , and .
Since , ,  etc. are  in UE5, external Blueprints
cannot access them directly. A subclass exposes public  /  event dispatchers.

---

## UE4 → UE5 Blueprint API Changes

| UE4 | UE5 | Notes |
|-----|-----|-------|
|  |  | Same pins |
|  |  (Buff System Interface) | Target = OwningCharacter, pass  |
|  |  (Buff System Interface) | Same as above |
|  | Removed | Widget lifecycle is automatic. Use  for cleanup |
|  |  | Also needs  first |
|  |  | Returns remaining seconds (float) |
|  |  | Same node, space removed from name |
|  |  | On SkeletalMeshComponent |
|  |  subclass pattern | See blueprints/ |
|  |  on widget instance | |
|  |  /  dispatchers | |

---

## Common Load Errors

### 
UE4 binary asset copied directly into UE5 project. Fix: export as CSV from UE4 devkit, reimport in UE5.

### 
Struct property GUIDs changed between UE4 and UE5. Fix: open the Blueprint, find the Make/Break struct node, right-click → Refresh Node.

### 
Animation sequence has corrupt frame rate from UE4→UE5 migration. Fix: enable  in Asset Details, or reimport from source FBX.

---

Made by [sibercat](https://github.com/sibercat) — ExilesExtreme mod author
