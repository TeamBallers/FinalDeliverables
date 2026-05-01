#!/usr/bin/env python3
"""
Script to process images through MASt3R-SLAM
Converts images to PNG format and runs the SLAM pipeline

Usage with uv:
    uv run process_images.py
    uv run process_images.py --input my_images/ --no-viz
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not found. Install with: uv pip install Pillow")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not found. Install with: uv pip install tqdm")
    print("Continuing without progress bars...\n")
    # Fallback if tqdm not available
    def tqdm(iterable, desc=""):
        print(f"{desc}...")
        return iterable


def convert_images(input_dir: Path, output_dir: Path) -> int:
    """Convert images from input_dir to PNG format in output_dir"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Supported image formats
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']

    # Find all images
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_dir.glob(f'*{ext}'))

    # Sort naturally
    image_files = sorted(image_files)

    if not image_files:
        print(f"Error: No images found in {input_dir}")
        return 0

    print(f"Found {len(image_files)} images")
    print("Converting to PNG format...")

    # Convert each image
    for img_path in tqdm(image_files, desc="Converting"):
        output_path = output_dir / f"{img_path.stem}.png"

        # If already PNG in correct location, skip
        if img_path.suffix.lower() == '.png' and img_path.parent == output_dir:
            continue

        try:
            # Open and save as PNG
            img = Image.open(img_path)
            width, height = img.size
            print(f"incoming w x h: {width} x {height}")
            # Convert to RGB if needed (handles RGBA, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            img = img.resize((512, 384), Image.BILINEAR)
            
            img.save(output_path, 'PNG')
            width, height = img.size
            print(f"saved w x h: {width} x {height}")
        except Exception as e:
            print(f"\nWarning: Failed to convert {img_path.name}: {e}")
            continue

    return len(image_files)


def run_slam(
    dataset_path: Path,
    config: str,
    save_as: str,
    calib: str = None,
    no_viz: bool = False
):
    """Run MASt3R-SLAM on the dataset"""
    cmd = [
        "python", "main.py",
        "--dataset", str(dataset_path),
        "--config", config,
        "--save-as", save_as
    ]

    if calib:
        cmd.extend(["--calib", calib])

    if no_viz:
        cmd.append("--no-viz")

    print("\n" + "=" * 50)
    print("Running MASt3R-SLAM...")
    print("Command:", " ".join(cmd))
    print("=" * 50 + "\n")

    # Run the command
    result = subprocess.run(cmd)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Process images through MASt3R-SLAM pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (with uv):
  # Process images from incoming_images directory
  uv run process_images.py

  # Process from custom directory with calibration
  uv run process_images.py --input my_images/ --calib config/intrinsics.yaml

  # Run without visualization (headless)
  uv run process_images.py --no-viz

  # Specify custom output name
  uv run process_images.py --save-as my_reconstruction

Examples (without uv):
  python process_images.py
  python process_images.py --input my_images/ --no-viz
        """
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("incoming_images"),
        help="Input directory with images (default: incoming_images)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("incoming_images_png"),
        help="Output directory for converted PNGs (default: incoming_images_png)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/base.yaml",
        help="Config YAML file (default: config/base.yaml)"
    )
    parser.add_argument(
        "--save-as",
        type=str,
        default="incoming_images_reconstruction",
        help="Save results as NAME (default: incoming_images_reconstruction)"
    )
    parser.add_argument(
        "--calib",
        type=str,
        default=None,
        help="Camera calibration file (optional)"
    )
    parser.add_argument(
        "--no-viz",
        action="store_true",
        help="Run without visualization"
    )
    parser.add_argument(
        "--skip-conversion",
        action="store_true",
        help="Skip image conversion (use if already converted to PNG)"
    )

    args = parser.parse_args()

    # Print configuration
    print("=" * 50)
    print("MASt3R-SLAM Image Processing Pipeline")
    print("=" * 50)
    print(f"Input directory:  {args.input}")
    print(f"Output directory: {args.output}")
    print(f"Config file:      {args.config}")
    print(f"Results name:     {args.save_as}")
    if args.calib:
        print(f"Calibration:      {args.calib}")
    print()

    # Check input directory exists
    if not args.input.exists():
        print(f"Error: Input directory '{args.input}' does not exist")
        sys.exit(1)

    # Convert images if not skipped
    if not args.skip_conversion:
        count = convert_images(args.input, args.output)
        if count == 0:
            sys.exit(1)
        print(f"Successfully converted {count} images\n")
    else:
        print("Skipping image conversion\n")

    # Run MASt3R-SLAM
    returncode = run_slam(
        args.output,
        args.config,
        args.save_as,
        args.calib,
        args.no_viz
    )

    # Print results
    if returncode == 0:
        print("\n" + "=" * 50)
        print("Processing complete!")
        print("=" * 50)
        print(f"Results saved to: logs/{args.save_as}/")
        print(f"  - Trajectory: logs/{args.save_as}/*.txt")
        print(f"  - Point cloud: logs/{args.save_as}/*.ply")
        print(f"  - Keyframes: logs/{args.save_as}/keyframes/")
    else:
        print("\n" + "=" * 50)
        print("Processing failed!")
        print("=" * 50)
        sys.exit(returncode)


if __name__ == "__main__":
    main()
