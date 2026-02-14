#!/bin/bash

# Script to convert Opus audio files to AAC (M4A format)
# Original Opus files are moved to processed folder

echo "========================================="
echo "Opus to AAC Converter"
echo "========================================="
echo ""
echo "Quality Settings:"
echo "  Audio: AAC, 192 kbps"
echo "  Format: M4A (MPEG-4 Audio)"
echo ""
echo "========================================="
echo ""

converted=0
failed=0

# Process all Opus files
for file in *.opus; do
    # Skip if no Opus files found
    if [ "$file" = "*.opus" ]; then
        echo "No Opus files found"
        exit 0
    fi

    echo "Processing: $file"

    # Get file size
    file_size=$(ls -lh "$file" | awk '{print $5}')
    echo "  Original size: $file_size"

    # Create output filename (replace .opus with .m4a)
    output_file="${file%.opus}.m4a"

    echo "  🎵 Converting to AAC (M4A)..."
    start_time=$(date +%s)

    # Convert to AAC
    if ffmpeg -v error -stats -i "$file" \
        -c:a aac -b:a 192k \
        -movflags +faststart \
        "$output_file" 2>&1; then

        end_time=$(date +%s)
        duration=$((end_time - start_time))

        # Get output file size
        output_size=$(ls -lh "$output_file" | awk '{print $5}')

        echo "  ✅ Successfully created: $output_file"
        echo "  📊 Output size: $output_size"
        echo "  ⏱️  Conversion time: ${duration} seconds"

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
echo "Summary:"
echo "========================================="
echo "✅ Converted to AAC: $converted"
echo "❌ Failed: $failed"
echo ""
if [ $converted -gt 0 ]; then
    echo "Original Opus files moved to: ./processed/"
    echo ""
    echo "Your M4A files are ready for:"
    echo "  • Apple Music/iTunes"
    echo "  • iPhone/iPad"
    echo "  • Any AAC-compatible player"
fi
