#!/bin/bash

# Script to process images through MASt3R-SLAM
# Converts JPEG images to PNG format and runs the SLAM pipeline

set -e  # Exit on error

# Configuration
INPUT_DIR="incoming_images"
OUTPUT_DIR="incoming_images_png"
CONFIG="config/base.yaml"
SAVE_AS="incoming_images_reconstruction"
CALIB=""  # Add path to calibration file if you have one

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --input)
            INPUT_DIR="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --save-as)
            SAVE_AS="$2"
            shift 2
            ;;
        --calib)
            CALIB="$2"
            shift 2
            ;;
        --no-viz)
            NO_VIZ="--no-viz"
            shift
            ;;
        --help)
            echo "Usage: ./process_images.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --input DIR       Input directory with images (default: incoming_images)"
            echo "  --output DIR      Output directory for converted PNGs (default: incoming_images_png)"
            echo "  --config FILE     Config YAML file (default: config/base.yaml)"
            echo "  --save-as NAME    Save results as NAME (default: incoming_images_reconstruction)"
            echo "  --calib FILE      Camera calibration file (optional)"
            echo "  --no-viz          Run without visualization"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "================================================"
echo "MASt3R-SLAM Image Processing Pipeline"
echo "================================================"
echo "Input directory:  $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Config file:      $CONFIG"
echo "Results will be saved as: $SAVE_AS"
echo ""

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

# Count images
IMAGE_COUNT=$(find "$INPUT_DIR" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | wc -l)
echo "Found $IMAGE_COUNT images in $INPUT_DIR"

if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "Error: No images found in $INPUT_DIR"
    exit 1
fi

# Create output directory
echo "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Convert images to PNG
echo "Converting images to PNG format..."
CONVERTED_COUNT=0
for img in "$INPUT_DIR"/*.{jpg,jpeg,JPG,JPEG,png,PNG} 2>/dev/null; do
    # Skip if glob didn't match any files
    [ -e "$img" ] || continue

    filename=$(basename "$img")
    filename_noext="${filename%.*}"

    # If already PNG, just copy
    if [[ "$img" == *.png ]] || [[ "$img" == *.PNG ]]; then
        cp "$img" "$OUTPUT_DIR/${filename_noext}.png"
    else
        # Convert JPEG to PNG using ImageMagick or ffmpeg
        if command -v convert &> /dev/null; then
            convert "$img" "$OUTPUT_DIR/${filename_noext}.png"
        elif command -v ffmpeg &> /dev/null; then
            ffmpeg -i "$img" -y "$OUTPUT_DIR/${filename_noext}.png" -loglevel quiet
        else
            echo "Error: Neither ImageMagick (convert) nor ffmpeg found."
            echo "Please install one of them:"
            echo "  sudo apt-get install imagemagick"
            echo "  or"
            echo "  sudo apt-get install ffmpeg"
            exit 1
        fi
    fi
    CONVERTED_COUNT=$((CONVERTED_COUNT + 1))
    echo "  Converted: $filename"
done

echo "Successfully converted $CONVERTED_COUNT images"
echo ""

# Build the command
CMD="python main.py --dataset $OUTPUT_DIR --config $CONFIG --save-as $SAVE_AS"

if [ -n "$CALIB" ]; then
    CMD="$CMD --calib $CALIB"
fi

if [ -n "$NO_VIZ" ]; then
    CMD="$CMD --no-viz"
fi

# Run MASt3R-SLAM
echo "================================================"
echo "Running MASt3R-SLAM..."
echo "Command: $CMD"
echo "================================================"
echo ""

$CMD

echo ""
echo "================================================"
echo "Processing complete!"
echo "================================================"
echo "Results saved to: logs/$SAVE_AS/"
echo "  - Trajectory: logs/$SAVE_AS/*.txt"
echo "  - Point cloud: logs/$SAVE_AS/*.ply"
echo "  - Keyframes: logs/$SAVE_AS/keyframes/"
