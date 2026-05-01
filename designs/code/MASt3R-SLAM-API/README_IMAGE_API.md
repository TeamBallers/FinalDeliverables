# MASt3R-SLAM Image Receiver API

Extensions to MASt3R-SLAM for receiving images via HTTP API and processing them continuously or in batches.

## Features

- **HTTP API** for receiving images on port 5050
- **Automatic conversion** from JPEG/PNG to PNG format
- **Continuous mode**: Auto-processes images after a delay
- **Batch mode**: Manually trigger processing
- **Status monitoring** via REST endpoints

## Quick Start

### 1. Install API Dependencies

```bash
conda activate mast3r-slam
pip install fastapi uvicorn[standard] python-multipart
```

### 2. Run the API Server

**Continuous Mode** (auto-processes after 5s idle):
```bash
python image_receiver_api.py --continuous
```

**Batch Mode** (manual processing):
```bash
python image_receiver_api.py
```

### 3. Send Images

```bash
# Upload an image
curl -X POST -F "file=@image.jpg" http://localhost:5050/upload

# Manually trigger processing (batch mode)
curl -X POST http://localhost:5050/process

# Check status
curl http://localhost:5050/status

# Clear all images
curl -X POST http://localhost:5050/clear
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/upload` | POST | Upload an image |
| `/process` | POST | Manually trigger SLAM processing |
| `/status` | GET | Get current status |
| `/clear` | POST | Clear all received images |

## Processing Modes

### Continuous Mode

Images are automatically processed after a delay (default 5 seconds) with no new images:

```bash
python image_receiver_api.py --continuous --delay 10
```

**Use case**: Real-time reconstruction as images arrive from a camera/drone

### Batch Mode

Images accumulate and you manually trigger processing:

```bash
python image_receiver_api.py
```

Then trigger when ready:
```bash
curl -X POST http://localhost:5050/process
```

**Use case**: Collect images first, then process in one batch

## Example: Streaming from a Camera

```python
import requests
import time
from pathlib import Path

# Send images as they're captured
for image_path in Path("camera_feed").glob("*.jpg"):
    with open(image_path, 'rb') as f:
        files = {'file': (image_path.name, f, 'image/jpeg')}
        response = requests.post('http://localhost:5050/upload', files=files)
        print(response.json())
    time.sleep(0.5)
```

## Simple Image Processing Script

Use the standalone `run_slam.py` script for processing existing image folders:

```bash
# Using uv (recommended)
uv run run_slam.py --input my_images/

# Without uv
python run_slam.py --input my_images/
```

Options:
- `--input`: Input directory with images
- `--output`: Output directory for converted PNGs
- `--config`: Config file (default: config/base.yaml)
- `--save-as`: Name for output
- `--calib`: Camera calibration file
- `--no-viz`: Run without visualization
- `--skip-conversion`: Skip PNG conversion

## Output

Results are saved to `logs/<save-as>/`:
- **Trajectory**: `*.txt` - Camera poses
- **Point Cloud**: `*.ply` - 3D reconstruction
- **Keyframes**: `keyframes/` - Extracted frames

## Architecture

```
┌─────────────┐
│   Client    │  Send images via POST
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  image_receiver_api.py  │  Port 5050
│  ├─ Receive images      │
│  ├─ Convert to PNG      │
│  └─ Queue/trigger SLAM  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│  MASt3R-SLAM (main.py)  │
│  └─ Process images      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│   logs/reconstruction/  │
│   ├─ trajectory.txt     │
│   ├─ pointcloud.ply     │
│   └─ keyframes/         │
└─────────────────────────┘
```

## Configuration

Server options:
- `--port`: Server port (default: 5050)
- `--continuous`: Enable auto-processing
- `--delay`: Seconds to wait before auto-processing (default: 5)

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'fastapi'`
**Solution**: Install API dependencies:
```bash
conda activate mast3r-slam
pip install fastapi uvicorn[standard] python-multipart
```

**Issue**: Images not processing
**Solution**: Check status endpoint and ensure conda environment is activated:
```bash
curl http://localhost:5050/status
```

**Issue**: SLAM fails to run
**Solution**: Ensure you're in the MASt3R-SLAM directory and have the `mast3r-slam` conda environment set up.

## Performance Notes

- **Continuous mode**: Best for real-time scenarios with steady image flow
- **Batch mode**: Better for large batches or when you want control over when processing starts
- Processing time depends on:
  - Number of images
  - GPU capability
  - Image resolution
  - Typical: ~2-5 minutes for 20-30 images on RTX 4090

## Credits

Built on top of [MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) by Riku Murai and Eric Dexheimer.
