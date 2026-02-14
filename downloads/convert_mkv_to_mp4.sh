#!/bin/bash

# Script to remux MKV files to MP4 if they contain H.264/H.265 video and AAC audio
# Original MKV files are moved to a "processed" subfolder

# Create processed folder if it doesn't exist
mkdir -p processed

converted=0
skipped=0
failed=0

echo "========================================="
echo "MKV to MP4 Remuxing Tool"
echo "========================================="
echo ""

# Process all MKV files
for file in *.mkv; do
    # Skip if no MKV files found
    if [ "$file" = "*.mkv" ]; then
        echo "No MKV files found"
        exit 0
    fi

    echo "Analyzing: $file"

    # Get video codec
    video_codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null)

    # Get audio codec
    audio_codec=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null)

    echo "  Video codec: $video_codec"
    echo "  Audio codec: $audio_codec"

    # Check if codecs are compatible with MP4
    video_compatible=false
    audio_compatible=false

    if [ "$video_codec" = "h264" ] || [ "$video_codec" = "hevc" ]; then
        video_compatible=true
    fi

    if [ "$audio_codec" = "aac" ]; then
        audio_compatible=true
    fi

    # If both are compatible, remux to MP4
    if [ "$video_compatible" = true ] && [ "$audio_compatible" = true ]; then
        # Create output filename (replace .mkv with .mp4)
        output_file="${file%.mkv}.mp4"

        echo "  ✅ Compatible! Remuxing to MP4..."

        # Remux without re-encoding
        if ffmpeg -v error -i "$file" -c copy -movflags +faststart "$output_file" 2>&1; then
            echo "  ✅ Successfully created: $output_file"

            # Move original MKV to processed folder
            mv "$file" "processed/"
            echo "  📁 Moved original to: processed/$file"

            ((converted++))
        else
            echo "  ❌ Failed to convert $file"
            # Remove partial output file if it exists
            rm -f "$output_file"
            ((failed++))
        fi
    else
        echo "  ⏭️  Skipping - incompatible codecs"
        if [ "$video_compatible" = false ]; then
            echo "     (Video codec '$video_codec' not compatible with MP4)"
        fi
        if [ "$audio_compatible" = false ]; then
            echo "     (Audio codec '$audio_codec' not compatible with MP4 - needs AAC)"
        fi
        ((skipped++))
    fi

    echo ""
done

echo "========================================="
echo "Summary:"
echo "========================================="
echo "✅ Converted to MP4: $converted"
echo "⏭️  Skipped (incompatible): $skipped"
echo "❌ Failed: $failed"
echo ""
if [ $converted -gt 0 ]; then
    echo "Original MKV files moved to: ./processed/"
fi
