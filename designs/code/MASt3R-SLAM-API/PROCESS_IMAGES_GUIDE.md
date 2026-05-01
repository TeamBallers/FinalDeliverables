# Processing Images with MASt3R-SLAM

Quick guide to processing your images through the MASt3R-SLAM pipeline using `uv`.

## Prerequisites

Install `uv` if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

Process your images from `incoming_images/` directory:

```bash
uv run process_images.py
```

That's it! The script will:
1. Convert JPEG/PNG images to the required PNG format
2. Run MASt3R-SLAM on the images
3. Save results to `logs/incoming_images_reconstruction/`

## Installing Dependencies

If this is your first run, `uv` will automatically create a virtual environment and install dependencies from `pyproject.toml`.

You can also manually install with:
```bash
# Sync all project dependencies
uv sync

# Or install specific packages
uv pip install Pillow tqdm
```

## Advanced Usage

### Custom input directory
```bash
uv run process_images.py --input path/to/your/images/
```

### With camera calibration
If you know your camera's intrinsic parameters, create `config/intrinsics.yaml`:
```yaml
width: 640
height: 480
# With distortion (fx, fy, cx, cy, k1, k2, p1, p2)
calibration: [517.3, 516.5, 318.6, 255.3, 0.2624, -0.9531, -0.0054, 0.0026, 1.1633]
```

Then run:
```bash
uv run process_images.py --calib config/intrinsics.yaml
```

### Headless mode (no visualization)
```bash
uv run process_images.py --no-viz
```

### Custom output name
```bash
uv run process_images.py --save-as my_room_scan
```

### All options combined
```bash
uv run process_images.py \
    --input my_images/ \
    --config config/base.yaml \
    --calib config/intrinsics.yaml \
    --save-as kitchen_reconstruction \
    --no-viz
```

## What the Script Does

1. **Image Conversion**: The MASt3R-SLAM dataloader only reads `.png` files, so the script:
   - Finds all JPEG and PNG images in your input directory
   - Converts them to PNG format
   - Saves to a temporary directory (default: `incoming_images_png/`)

2. **SLAM Processing**: Runs the main MASt3R-SLAM pipeline with your images

3. **Output**: Creates a 3D reconstruction and saves:
   - Camera trajectory (`.txt`)
   - 3D point cloud (`.ply`)
   - Keyframe images

## Output Files

After processing, find your results in `logs/<save-as>/`:
```
logs/incoming_images_reconstruction/
├── trajectory.txt          # Camera poses over time
├── pointcloud.ply         # 3D reconstruction
└── keyframes/             # Extracted keyframes
    └── frame_0000.png
    └── frame_0001.png
    └── ...
```

## Viewing Results

Open the `.ply` file with any point cloud viewer:
- [MeshLab](https://www.meshlab.net/)
- [CloudCompare](https://www.cloudcompare.org/)
- [Open3D](http://www.open3d.org/)

## Troubleshooting

### "No images found"
Make sure your images are in the correct directory and are `.jpg`, `.jpeg`, or `.png` format.

### Missing dependencies
Run `uv sync` to install all required packages.

### CUDA/GPU errors
MASt3R-SLAM requires a CUDA-capable GPU. Check your PyTorch installation:
```bash
uv run python -c "import torch; print(torch.cuda.is_available())"
```

## Using without uv

If you prefer traditional Python:
```bash
python process_images.py
```

Just make sure you've installed the dependencies:
```bash
pip install Pillow tqdm
```
