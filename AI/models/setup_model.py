
import os
import shutil

from ultralytics import YOLO

# -- Configuration ------------------------------------------------------------
MODEL_NAME = "yolov8s.pt"
MODEL_DIR  = os.path.dirname(os.path.abspath(__file__))  # AI/models/
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)

# -- Download / Load ----------------------------------------------------------
print("=" * 60)
print("  FootVision AI - Model Setup")
print("=" * 60)
print(f"\n[1/3] Target model : {MODEL_NAME}")
print(f"[1/3] Target path  : {MODEL_PATH}")

if os.path.exists(MODEL_PATH):
    print(f"\n[1/3] Model already exists locally - loading from disk.")
    model = YOLO(MODEL_PATH)
else:
    print(f"\n[1/3] Model not found locally - downloading from Ultralytics (~21 MB)...")
    print("      This may take a minute on first run.\n")
    # Ultralytics downloads to the current working directory by default
    model = YOLO(MODEL_NAME)

    # Move into AI/models/ if it landed in the project root
    downloaded_in_root = os.path.join(os.getcwd(), MODEL_NAME)
    if os.path.exists(downloaded_in_root) and not os.path.exists(MODEL_PATH):
        shutil.move(downloaded_in_root, MODEL_PATH)
        print(f"\n[1/3] Model moved to {MODEL_PATH}")
        model = YOLO(MODEL_PATH)

# -- Verification -------------------------------------------------------------
print("\n[2/3] Verifying model...")

assert os.path.exists(MODEL_PATH), f"Model file not found at {MODEL_PATH}"

file_size_mb = os.path.getsize(MODEL_PATH) / 1e6
assert file_size_mb > 5, f"Model file too small ({file_size_mb:.1f} MB) - may be corrupt."

assert model.task == "detect", f"Unexpected task: {model.task} (expected 'detect')"

has_person = "person" in model.names.values()
assert has_person, "'person' class not found in model - wrong weights?"

# -- Summary ------------------------------------------------------------------
print("\n" + "=" * 60)
print("  VERIFICATION PASSED")
print("=" * 60)
print(f"\n  Model name    : {MODEL_NAME}")
print(f"  Task          : {model.task}")
print(f"  File size     : {file_size_mb:.1f} MB")
print(f"  Total classes : {len(model.names)}")
print(f"  Has 'person'  : {has_person}  <- players will be detected as this class")
print(f"  Saved at      : {MODEL_PATH}")
print("\n[3/3] YOLOv8s is ready. Report back to proceed to Step 3.")
print("=" * 60)

