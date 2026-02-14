#!/bin/bash

# Script to process MKV files:
# - Real videos get renamed with (Video) suffix
# - Static image videos get audio extracted and original deleted

# Find all MKV files without "Video" in their name
while IFS= read -r -d '' file; do
    echo "Processing: $file"

    # Get just the filename without path
    filename=$(basename "$file")

    # Use ffmpeg to extract 3 frames (at 10%, 50%, 90% of duration) and compare them
    # If frames are very similar, it's likely a static image
    # This is faster than full scene detection

    # Get duration in seconds
    duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$file")

    if [ -z "$duration" ] || [ "$duration" = "N/A" ]; then
        echo "  ⚠️  Could not determine duration, skipping"
        continue
    fi

    # Calculate time points (10%, 50%, 90%)
    t1=$(echo "$duration * 0.1" | bc)
    t2=$(echo "$duration * 0.5" | bc)
    t3=$(echo "$duration * 0.9" | bc)

    # Extract frames to temp directory
    temp_dir=$(mktemp -d)
    ffmpeg -v error -ss "$t1" -i "$file" -vframes 1 -f image2 "$temp_dir/frame1.png" 2>/dev/null
    ffmpeg -v error -ss "$t2" -i "$file" -vframes 1 -f image2 "$temp_dir/frame2.png" 2>/dev/null
    ffmpeg -v error -ss "$t3" -i "$file" -vframes 1 -f image2 "$temp_dir/frame3.png" 2>/dev/null

    # Compare frames using perceptual hash difference
    # If all 3 frames exist and are identical (or very similar), it's static
    if [ -f "$temp_dir/frame1.png" ] && [ -f "$temp_dir/frame2.png" ] && [ -f "$temp_dir/frame3.png" ]; then
        # Compare file sizes as a quick check (identical frames = identical file sizes)
        size1=$(stat -f%z "$temp_dir/frame1.png" 2>/dev/null || stat -c%s "$temp_dir/frame1.png" 2>/dev/null)
        size2=$(stat -f%z "$temp_dir/frame2.png" 2>/dev/null || stat -c%s "$temp_dir/frame2.png" 2>/dev/null)
        size3=$(stat -f%z "$temp_dir/frame3.png" 2>/dev/null || stat -c%s "$temp_dir/frame3.png" 2>/dev/null)

        # Calculate size difference percentage
        max_diff=0
        for s1 in $size1 $size2; do
            for s2 in $size2 $size3; do
                if [ "$s1" -gt "$s2" ]; then
                    diff=$(echo "scale=2; ($s1 - $s2) * 100 / $s1" | bc)
                else
                    diff=$(echo "scale=2; ($s2 - $s1) * 100 / $s2" | bc)
                fi
                if (( $(echo "$diff > $max_diff" | bc -l) )); then
                    max_diff=$diff
                fi
            done
        done

        # If frames differ by less than 5%, consider it static
        if (( $(echo "$max_diff < 5" | bc -l) )); then
            echo "  📷 Static image detected (frame diff: ${max_diff}%)"

            # Extract audio without re-encoding
            # Remove .mkv extension and add appropriate audio extension
            base_name="${filename%.mkv}"

            # Detect audio codec to determine extension
            audio_codec=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$file")

            case "$audio_codec" in
                aac)
                    ext="m4a"
                    ;;
                mp3)
                    ext="mp3"
                    ;;
                opus)
                    ext="opus"
                    ;;
                vorbis)
                    ext="ogg"
                    ;;
                flac)
                    ext="flac"
                    ;;
                *)
                    ext="mka"  # Matroska audio container for unknown codecs
                    ;;
            esac

            output_file="${base_name}.${ext}"

            # Extract audio
            echo "  🎵 Extracting audio to: $output_file"
            if ffmpeg -v error -i "$file" -vn -acodec copy "$output_file"; then
                echo "  ✅ Audio extracted successfully"
                echo "  🗑️  Deleting original MKV: $filename"
                rm "$file"
            else
                echo "  ❌ Failed to extract audio"
            fi
        else
            echo "  🎬 Motion video detected (frame diff: ${max_diff}%)"

            # Rename with (Video) suffix
            base_name="${filename%.mkv}"
            new_name="${base_name} (Video).mkv"

            echo "  ✏️  Renaming to: $new_name"
            mv "$file" "$new_name"
        fi
    else
        echo "  ⚠️  Could not extract frames, skipping"
    fi

    # Cleanup temp directory
    rm -rf "$temp_dir"
    echo ""

done < <(find . -maxdepth 1 -name "*.mkv" ! -name "*Video*" -type f -print0)

echo "✅ Processing complete!"
