# from fastapi import FastAPI, File, UploadFile
# from fastapi.staticfiles import StaticFiles
# from ultralytics import YOLO
# import numpy as np
# from PIL import Image
# import io
# from datetime import datetime
# from pathlib import Path
# import torch
# from fastapi.middleware.cors import CORSMiddleware
# import time

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # for dev 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ----------------------------
# # PATH SETUP
# # ----------------------------
# BASE_DIR = Path(__file__).resolve().parent

# RUNS_DIR = BASE_DIR / "runs"
# BASE = RUNS_DIR / "api_outputs"

# RAW_DIR = BASE / "raw"
# ANN_DIR = BASE / "annotated"

# RAW_DIR.mkdir(parents=True, exist_ok=True)
# ANN_DIR.mkdir(parents=True, exist_ok=True)

# DATASET_DIR = BASE_DIR / "incoming_images_png"
# DATASET_DIR.mkdir(exist_ok=True)

# # ----------------------------
# # STATIC FILE ACCESS
# # ----------------------------
# app.mount(
#     "/runs",
#     StaticFiles(directory=RUNS_DIR),
#     name="runs"
# )

# # ----------------------------
# # DEVICE
# # ----------------------------
# if torch.backends.mps.is_available():
#     DEVICE = "mps"
# elif torch.cuda.is_available():
#     DEVICE = "cuda"
# else:
#     DEVICE = "cpu"

# print(f"Using device: {DEVICE}")

# # ----------------------------
# # MODEL
# # ----------------------------
# model = YOLO("yolo11s.pt")
# model.to(DEVICE)

# # ----------------------------
# # ROOT
# # ----------------------------
# @app.get("/")
# def root():
#     return {"status": "YOLO server running", "device": DEVICE}

# # OPTIONAL: LIST IMAGES FOR FRONTEND
# @app.get("/images")
# def list_images():
#     files = sorted(ANN_DIR.glob("*.jpg"))

#     return [
#         {
#             "filename": f.name,
#             "url": f"/runs/api_outputs/annotated/{f.name}"
#         }
#         for f in files
#     ]

# # ----------------------------
# # DETECT
# # ----------------------------
# @app.post("/detect")
# async def detect(file: UploadFile = File(...)):

#     image_bytes = await file.read()
#     image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     image_np = np.array(image)

#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

#     # SAVE RAW IMAGE
#     raw_path = RAW_DIR / f"raw_{timestamp}.jpg"
#     image.save(raw_path)

#     # RUN YOLO
#     results = model(image_np)
#     r = results[0]

#     detections = []
#     for box in r.boxes:
#         cls_id = int(box.cls[0])
#         conf = float(box.conf[0])

#         detections.append({
#             "class_id": cls_id,
#             "class_name": model.names[cls_id],
#             "confidence": conf,
#             "bbox": box.xyxy[0].tolist()
#         })

#     # ANNOTATED IMAGE
#     annotated_img = r.plot()
#     annotated_pil = Image.fromarray(annotated_img)

#     annotated_path = ANN_DIR / f"annotated_{timestamp}.jpg"
#     annotated_pil.save(annotated_path)

#     # RETURN URLs (IMPORTANT FOR FRONTEND)
#     return { 
#         "detections": detections,
#         "num_detections": len(detections),

#         "raw_image": f"/runs/api_outputs/raw/{raw_path.name}",
#         "annotated_image": f"/runs/api_outputs/annotated/{annotated_path.name}",

#         "device": DEVICE
#     }

#!/usr/bin/env python3
"""
YOLO background watcher service.

- Watches: incoming_images_png/ (project root)
- Writes: runs/api_outputs/annotated/
- No upload endpoint needed
- Fully compatible with image_receiver_api.py
"""

import time
import threading
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image, ImageFile
import torch
from ultralytics import YOLO

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# ----------------------------
# SAFETY: handle partial PIL reads
# ----------------------------
ImageFile.LOAD_TRUNCATED_IMAGES = True

# ----------------------------
# FASTAPI APP
# ----------------------------
app = FastAPI(title="YOLO Watcher Service")

# ----------------------------
# CORS Middleware permission
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# PATH SETUP (IMPORTANT: PROJECT ROOT)
# ----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

WATCH_DIR = PROJECT_ROOT / "incoming_images_png"

RUNS_DIR = PROJECT_ROOT / "runs"
ANN_DIR = RUNS_DIR / "api_outputs" / "annotated"

RUNS_DIR.mkdir(parents=True, exist_ok=True)
ANN_DIR.mkdir(parents=True, exist_ok=True)


print("PROJECT ROOT:", PROJECT_ROOT)
print("ANN DIR:", ANN_DIR.resolve())


# ----------------------------
# STATIC FILES (FOR VIEWER)
# ----------------------------
app.mount(
    "/runs",
    StaticFiles(directory=RUNS_DIR),
    name="runs"
)

# ----------------------------
# DEVICE SETUP
# ----------------------------
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"

print(f"[YOLO] Using device: {DEVICE}")

# ----------------------------
# MODEL
# ----------------------------
model = YOLO("yolo11s.pt")
model.to(DEVICE)

# ----------------------------
# STATE
# ----------------------------
seen_files = set()
running = True

# IMPORTANT FIX: wait for file to fully finish writing
MIN_FILE_AGE_SEC = 1.0


# ----------------------------
# YOLO PROCESSING
# ----------------------------
def process_image(img_path: Path):
    """Run YOLO on one image and save annotated result."""

    try:
        image = Image.open(img_path).convert("RGB")
        image_np = np.array(image)

        results = model(image_np)
        r = results[0]
        LIVING_CLASSES = {"person", "cat", "dog", "bird", "horse", "sheep", "cow"}

        has_living = False

        for box in r.boxes:
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]

            if cls_name in LIVING_CLASSES:
                has_living = True
                break

        annotated = r.plot()
        annotated_pil = Image.fromarray(annotated)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_path = ANN_DIR / f"annotated_{timestamp}.jpg"

        annotated_pil.save(out_path)
        meta_path = ANN_DIR / f"annotated_{timestamp}.txt"
        meta_path.write_text("living=1" if has_living else "living=0")

        print(f"🧠 YOLO processed: {img_path.name} -> {out_path.name}")

    except Exception as e:
        print(f"❌ YOLO error on {img_path.name}: {e}")


# ----------------------------
# WATCHER LOOP
# ----------------------------
def watcher_loop():
    """Watch incoming_images_png safely and process stable files only."""

    print("👀 YOLO watcher started...")
    print(f"📂 Watching: {WATCH_DIR}")

    global seen_files

    while running:
        try:
            images = sorted(WATCH_DIR.glob("*.png"))

            now = time.time()

            for img in images:
                if img in seen_files:
                    continue

                try:
                    # skip empty files
                    if img.stat().st_size == 0:
                        continue

                    # FIX: ensure file is fully written using mtime
                    age = now - img.stat().st_mtime
                    if age < MIN_FILE_AGE_SEC:
                        continue

                except FileNotFoundError:
                    continue

                seen_files.add(img)

                process_image(img)

            time.sleep(0.5)

        except Exception as e:
            print(f"⚠️ Watcher error: {e}")
            time.sleep(1)


# ----------------------------
# ROOT (HEALTH CHECK)
# ----------------------------
@app.get("/")
def root():
    return {
        "status": "YOLO watcher running",
        "watch_dir": str(WATCH_DIR),
        "output_dir": str(ANN_DIR),
        "device": DEVICE
    }


# ----------------------------
# LIST IMAGES (FRONTEND)
# ----------------------------
@app.get("/images")
def list_images():
    # files = sorted(ANN_DIR.glob("*.jpg"))

    # return [
    #     {
    #         "filename": f.name,
    #         "url": f"/runs/api_outputs/annotated/{f.name}"
    #     }
    #     for f in files
    # ]
    files = sorted(ANN_DIR.glob("*.jpg"))

    result = []

    for f in files:
        meta = ANN_DIR / f"{f.stem}.txt"

        if not meta.exists():
            continue

        try:
            if meta.read_text().strip() == "living=1":
                result.append({
                    "filename": f.name,
                    "url": f"/runs/api_outputs/annotated/{f.name}"
                })
        except:
            continue

    return result

@app.post("/delete")
def reset_seen():
    import shutil
    shutil.rmtree(ANN_DIR)
    ANN_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------
# START SERVICE
# ----------------------------
def main():
    global running

    thread = threading.Thread(target=watcher_loop, daemon=True)
    thread.start()

    print("🚀 YOLO service starting on http://0.0.0.0:8000")
    print("📡 Waiting for images from image_receiver_api.py...")

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()