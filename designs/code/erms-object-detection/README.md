# ERMS Object Detection Pipeline (Raspberry Pi + YOLO Server)

This project implements a distributed real-time object detection system using a Raspberry Pi and a FastAPI server running YOLO.

---

# System Overview

The system follows an edge-to-server architecture:

- **Raspberry Pi (Client)**  
  Captures images using a camera and sends them to the server.

- **Server (Mac / Laptop)**  
  Runs YOLO object detection using FastAPI and returns results.

---

# Pipeline Flow

1. Raspberry Pi captures image using Picamera2
2. Image is sent via HTTP POST request to server
3. FastAPI server receives image
4. YOLO model performs object detection
5. Server saves:
   - raw image
   - annotated image (with bounding boxes)
6. Server returns JSON response with detections

---

# Project Structure

```text id="struct1"
erms-object-detection/
│
├── server/
│   ├── yolo_api.py
│   ├── requirements.txt
│   └── README.md
│
├── client/
│   └── test_yolo_pipeline.py
│
├── .gitignore
└── README.md