from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO
import numpy as np
from PIL import Image
import io
from datetime import datetime
from pathlib import Path
import torch
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# PATH SETUP
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent

RUNS_DIR = BASE_DIR / "runs"
BASE = RUNS_DIR / "api_outputs"

RAW_DIR = BASE / "raw"
ANN_DIR = BASE / "annotated"

RAW_DIR.mkdir(parents=True, exist_ok=True)
ANN_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------
# STATIC FILE ACCESS
# ----------------------------
app.mount(
    "/runs",
    StaticFiles(directory=RUNS_DIR),
    name="runs"
)

# ----------------------------
# DEVICE
# ----------------------------
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"

print(f"Using device: {DEVICE}")

# ----------------------------
# MODEL
# ----------------------------
model = YOLO("yolo11s.pt")
model.to(DEVICE)

# ----------------------------
# ROOT
# ----------------------------
@app.get("/")
def root():
    return {"status": "YOLO server running", "device": DEVICE}

# OPTIONAL: LIST IMAGES FOR FRONTEND
@app.get("/images")
def list_images():
    files = sorted(ANN_DIR.glob("*.jpg"))

    return [
        {
            "filename": f.name,
            "url": f"/runs/api_outputs/annotated/{f.name}"
        }
        for f in files
    ]

# ----------------------------
# DETECT
# ----------------------------
@app.post("/detect")
async def detect(file: UploadFile = File(...)):

    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_np = np.array(image)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # SAVE RAW IMAGE
    raw_path = RAW_DIR / f"raw_{timestamp}.jpg"
    image.save(raw_path)

    # RUN YOLO
    results = model(image_np)
    r = results[0]

    detections = []
    for box in r.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        detections.append({
            "class_id": cls_id,
            "class_name": model.names[cls_id],
            "confidence": conf,
            "bbox": box.xyxy[0].tolist()
        })

    # ANNOTATED IMAGE
    annotated_img = r.plot()
    annotated_pil = Image.fromarray(annotated_img)

    annotated_path = ANN_DIR / f"annotated_{timestamp}.jpg"
    annotated_pil.save(annotated_path)

    # RETURN URLs (IMPORTANT FOR FRONTEND)
    return {
        "detections": detections,
        "num_detections": len(detections),

        "raw_image": f"/runs/api_outputs/raw/{raw_path.name}",
        "annotated_image": f"/runs/api_outputs/annotated/{annotated_path.name}",

        "device": DEVICE
    }