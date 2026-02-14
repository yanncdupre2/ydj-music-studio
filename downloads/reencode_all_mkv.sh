#!/bin/bash

# Script to re-encode ALL remaining MKV files to MP4 with optimized quality settings
# - Audio: AAC 192kbps (good quality for web sources)
# - Video: Max 1080p resolution, CRF based on file size
# - CRF 21 for files < 50MB, CRF 22 for files >= 50MB

echo "========================================="
echo "MKV to MP4 Batch Re-encoding (Optimized)"
echo "========================================="
echo ""
echo "Quality Settings:"
echo "  Audio: AAC, 192 kbps"
echo "  Video: H.264, max 1080p resolution"
echo "  CRF: 21 (files <50MB), 22 (files ≥50MB)"
echo ""

# Count total files
total_files=$(ls -1 *.mkv 2>/dev/null | wc -l | tr -d ' ')
echo "Found $total_files MKV files to process"
echo ""
echo "========================================="
echo ""

converted=0
failed=0
current=0

# Process all MKV files
for file in *.mkv; do
    # Skip if no MKV files found
    if [ "$file" = "*.mkv" ]; then
        echo "No MKV files found"
        exit 0
    fi

    ((current++))
    echo "[$current/$total_files] Processing: $file"

    # Get file size in bytes
    file_size_bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    file_size_mb=$((file_size_bytes / 1048576))
    file_size_human=$(ls -lh "$file" | awk '{print $5}')

    echo "  Original size: $file_size_human (${file_size_mb}MB)"

    # Determine CRF based on file size (50MB threshold)
    if [ $file_size_bytes -lt 52428800 ]; then
        crf=21
        echo "  CRF: 21 (file < 50MB)"
    else
        crf=22
        echo "  CRF: 22 (file ≥ 50MB)"
    fi

    # Get video resolution
    width=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null)
    height=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null)

    # Get codecs info
    video_codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null)
    audio_codec=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null)

    echo "  Source: ${width}x${height}, $video_codec video, $audio_codec audio"

    # Determine if we need to scale down to 1080p
    if [ -n "$height" ] && [ "$height" -gt 1080 ]; then
        scale_filter="scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease"
        echo "  📐 Scaling down to max 1080p"
    else
        scale_filter=""
        echo "  📐 Keeping original resolution (≤1080p)"
    fi

    # Create output filename
    output_file="${file%.mkv}.mp4"

    echo "  🎬 Re-encoding to MP4..."
    start_time=$(date +%s)

    # Build ffmpeg command
    if [ -n "$scale_filter" ]; then
        # With scaling
        ffmpeg -v error -stats -i "$file" \
            -vf "$scale_filter" \
            -c:v libx264 -crf $crf -preset medium \
            -c:a aac -b:a 192k \
            -movflags +faststart \
            -y \
            "$output_file" 2>&1
    else
        # No scaling needed
        ffmpeg -v error -stats -i "$file" \
            -c:v libx264 -crf $crf -preset medium \
            -c:a aac -b:a 192k \
            -movflags +faststart \
            -y \
            "$output_file" 2>&1
    fi

    if [ $? -eq 0 ]; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))

        # Get output file size
        output_size_bytes=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
        output_size_mb=$((output_size_bytes / 1048576))
        output_size_human=$(ls -lh "$output_file" | awk '{print $5}')

        # Calculate size ratio
        if [ $file_size_bytes -gt 0 ]; then
            size_ratio=$((output_size_bytes * 100 / file_size_bytes))
        else
            size_ratio=0
        fi

        echo "  ✅ Successfully created: $output_file"
        echo "  📊 Output size: $output_size_human (${output_size_mb}MB) - ${size_ratio}% of original"
        echo "  ⏱️  Encoding time: ${duration} seconds"

        # Move original to processed folder
        mv "$file" "processed/"
        echo "  📁 Moved original to: processed/$file"

        ((converted++))
    else
        echo "  ❌ Failed to convert $file"
        # Remove partial output file if it exists
        rm -f "$output_file"
        ((failed++))
    fi

    echo ""
done

echo "========================================="
echo "Final Summary:"
echo "========================================="
echo "✅ Successfully re-encoded: $converted"
echo "❌ Failed: $failed"
echo "📁 Total processed: $((converted + failed)) / $total_files"
echo ""
if [ $converted -gt 0 ]; then
    echo "All original MKV files moved to: ./processed/"
    echo ""
    echo "Settings used:"
    echo "  🎧 Audio: AAC 192kbps"
    echo "  🎬 Video: H.264, CRF 21/22, max 1080p"
    echo ""
    echo "Your MP4 files are ready for Apple Music!"
fi
