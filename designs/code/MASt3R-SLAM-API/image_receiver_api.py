#!/usr/bin/env python3
"""
API server to receive images via POST requests and queue them for SLAM processing.

Usage:
    # With continuous processing
    python image_receiver_api.py --continuous

    # Batch mode (process manually)
    python image_receiver_api.py
"""

import argparse
import io
import os
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
import glob
import shutil

from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import uvicorn

app = FastAPI(title="MASt3R-SLAM Image Receiver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
INCOMING_DIR = Path("incoming_images")
PNG_DIR = Path("incoming_images_png")
INCOMING_DIR.mkdir(exist_ok=True)
PNG_DIR.mkdir(exist_ok=True)

# Global state for continuous processing
continuous_mode = False
processing_lock = threading.Lock()
is_processing = False
previous_img_count = 0

# Global state for copy functionality
copy_mode = False
copy_path = None


def convert_to_png(image_data: bytes, filename: str) -> Path:
    """Convert image to PNG and save to PNG directory."""
    # Open image
    img = Image.open(io.BytesIO(image_data))

    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stem = Path(filename).stem
    png_filename = f"{stem}_{timestamp}.png"
    png_path = PNG_DIR / png_filename

    # Save as PNG
    img.save(png_path, 'PNG')

    return png_path


def run_slam_processing():
    """Run MASt3R-SLAM on collected images."""
    global is_processing

    with processing_lock:
        if is_processing:
            print("⚠️  Processing already running, skipping...")
            return
        is_processing = True

    try:
        print("\n" + "="*50)
        print("🚀 Starting MASt3R-SLAM processing...")
        print("="*50)

        # Count images
        image_count = len(list(PNG_DIR.glob("*.png")))
        print(f"📊 Processing {image_count} images")

        global previous_img_count
        if image_count < previous_img_count + 40:
            print("⚠️  Not enough new images to process")
            return
        else:  
            print(f"📈 New images detected: {image_count - previous_img_count}")
        previous_img_count = image_count

        # Run SLAM
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_name = f"reconstruction_{timestamp}"

        cmd = [
            "conda", "run", "-n", "mast3r-slam", "--no-capture-output",
            "python", "main.py",
            "--dataset", str(PNG_DIR),
            "--config", "config/base.yaml",
            "--save-as", save_name
        ]

        print(f"🔧 Command: {' '.join(cmd)}")

        result = subprocess.run(cmd)

        if result.returncode == 0:
            print("\n" + "="*50)
            print("✅ Processing complete!")
            print("="*50)
            print(f"📁 Results saved to: logs/{save_name}/")
            print(f"  - Trajectory: logs/{save_name}/*.txt")
            print(f"  - Point cloud: logs/{save_name}/*.ply")
            print(f"  - Keyframes: logs/{save_name}/keyframes/")

            # Copy ply file if copy mode is enabled
            if copy_mode and copy_path:
                ply_files = glob.glob(f"logs/{save_name}/*.ply")
                if ply_files:
                    ply_file = ply_files[0]
                    shutil.copy2(ply_file, copy_path)
                    print(f"Copied ply file to: {copy_path}")
                else:
                    print("No ply file found to copy")
        else:
            print("\n" + "="*50)
            print("❌ Processing failed!")
            print("="*50)
            print(f"Return code: {result.returncode}")

    finally:
        with processing_lock:
            is_processing = False

def continuous_processor():
    """Background thread that runs SLAM every fixed interval."""
    interval = 5  # seconds

    while continuous_mode:
        time.sleep(interval)

        # Only run if not already processing
        with processing_lock:
            if is_processing:
                print("⚠️  Previous processing still running, skipping this cycle...")
                continue

        run_slam_processing()


def clear_image_dirs():
    import shutil

    for path in [INCOMING_DIR, PNG_DIR]:
        if path.exists():
            shutil.rmtree(path)
            path.mkdir()

    global previous_img_count
    previous_img_count = 0


@app.post("/upload")
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Receive an image via POST request.

    Example:
        curl -X POST -F "file=@image.jpg" http://localhost:5050/upload
    """

    try:
        # Read image data
        image_data = await file.read()

        # Save original
        original_path = INCOMING_DIR / file.filename
        with open(original_path, 'wb') as f:
            f.write(image_data)

        # Convert to PNG
        png_path = convert_to_png(image_data, file.filename)

        print(f"✅ Received and converted: {file.filename} -> {png_path.name}")

        return JSONResponse(content={
            "status": "success",
            "message": f"Image received and converted to PNG",
            "original": str(original_path),
            "png": str(png_path),
            "total_images": len(list(PNG_DIR.glob("*.png")))
        })

    except Exception as e:
        print(f"❌ Error processing {file.filename}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )


@app.post("/process")
async def trigger_process(background_tasks: BackgroundTasks):
    """
    Manually trigger SLAM processing.

    Example:
        curl -X POST http://localhost:5050/process
    """
    background_tasks.add_task(run_slam_processing)

    return JSONResponse(content={
        "status": "success",
        "message": "Processing started in background"
    })


@app.get("/status")
async def get_status():
    """Get current status."""
    model_path = Path.home() / "ply_viewer" / "model.ply"
    return JSONResponse(content={
        "continuous_mode": continuous_mode,
        "is_processing": is_processing,
        "model_exists": model_path.exists(),
        "total_images": len(list(PNG_DIR.glob("*.png"))),
        "incoming_images": len(list(INCOMING_DIR.glob("*"))),
    })


@app.post("/clear")
async def clear_images():
    """Clear all received images."""
    clear_image_dirs()
    if os.path.exists("../ply_viewer/model.ply"):
        os.remove("../ply_viewer/model.ply")

    return JSONResponse(content={
        "status": "success",
        "message": "All images cleared"
    })


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MASt3R-SLAM Image Receiver",
        "endpoints": {
            "POST /upload": "Upload an image",
            "POST /process": "Manually trigger processing",
            "GET /status": "Get current status",
            "POST /clear": "Clear all images",
        },
        "continuous_mode": continuous_mode
    }


def main():
    global continuous_mode
    global copy_mode
    global copy_path

    parser = argparse.ArgumentParser(description="MASt3R-SLAM Image Receiver API")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Enable continuous processing mode (auto-process after delay)"
    )
    parser.add_argument(
        "--copy",
        type=str,
        default=None,
        help="Path with filename to copy processed ply to"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Delay in seconds before auto-processing (default: 5)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5050,
        help="Port to run server on (default: 5050)"
    )

    args = parser.parse_args()

    continuous_mode = args.continuous
    global process_delay
    process_delay = args.delay
    
    if args.copy:
        copy_mode = True
        copy_path = Path(args.copy)
        copy_path.parent.mkdir(exist_ok=True, parents=True)
        if copy_path.exists():
            import os
            os.remove(copy_path)
        print(f"Will copy resulting *.ply model to: {copy_path}")

    # Start continuous processor thread if enabled
    if continuous_mode:
        print("🔄 Continuous processing mode ENABLED")
        print(f"⏱️  Will auto-process {process_delay}s after last image")
        processor_thread = threading.Thread(target=continuous_processor, daemon=True)
        processor_thread.start()
    else:
        print("📦 Batch mode - use POST /process to trigger processing")

    clear_image_dirs()

    print(f"🌐 Starting server on http://0.0.0.0:{args.port}")
    print("\nExample usage:")
    print(f"  curl -X POST -F 'file=@image.jpg' http://localhost:{args.port}/upload")
    print(f"  curl -X POST http://localhost:{args.port}/process")
    print(f"  curl http://localhost:{args.port}/status")

    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()