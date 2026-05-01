# YOLO Server (FastAPI)

This folder contains the backend server that runs YOLO object detection.

---

## What it does

- Receives images from Raspberry Pi (client)
- Runs YOLO inference
- Saves:
  - raw images
  - annotated images
- Returns detections via JSON

---

# Setup Instructions

## 1. Install dependencies

Run the following command inside the `server/` directory:

```bash
pip install -r requirements.txt
```

## 2. Start the venv and server (still in server folder)
```bash
python3 -m venv yolo_env
source yolo_env/bin/activate
uvicorn yolo_api:app --host 0.0.0.0 --port 8000
```
The server will run at:
```bash
http://<YOUR_IP>:8000
```

## 3. API Usage
Endpoint: `/detect`
Example request:
```bash
curl -X POST "http://<SERVER_IP>:8000/detect" -F "file=@test.jpg"
```
Response Format:
```bash
{
  "num_detections": 3,
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.92,
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "raw_image": "runs/api_outputs/raw/...",
  "annotated_image": "runs/api_outputs/annotated/..."
}
```

Output Structre:
```bash
runs/
└── api_outputs/
    ├── raw/
    └── annotated/
```
