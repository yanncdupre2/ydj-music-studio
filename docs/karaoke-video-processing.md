# Karaoke Video Processing — ffmpeg Filter Reference

## Goal

Prepare karaoke videos for overlay blending onto music videos in Final Cut Pro.
Requirements for the overlay to work well:
- Pure black background (becomes transparent in screen/add blend modes)
- Bright, high-contrast text with glow effect
- Sung text in bright green (easily distinguishable from white unsung text)
- Channel logos/watermarks masked out

## Final Filter Pipeline (v10)

Developed April 2026. Tested on "Musisi Karaoke" channel videos (orange sung → white unsung, black background, logo in lower-left).

### Full ffmpeg command

```bash
ffmpeg -i "input.mp4" \
  -filter_complex "
    [0:v] format=gbrp,
          drawbox=x=0:y=ih-300:w=330:h=300:color=black:t=fill,
          geq=r='if(gt(r(X,Y), 1.3*g(X,Y)) * gt(r(X,Y), 2*b(X,Y)) * gt(r(X,Y), 80), b(X,Y)*0.2, r(X,Y))'
              :g='if(gt(r(X,Y), 1.3*g(X,Y)) * gt(r(X,Y), 2*b(X,Y)) * gt(r(X,Y), 80), clip(r(X,Y)*1.1, 0, 255), g(X,Y))'
              :b='if(gt(r(X,Y), 1.3*g(X,Y)) * gt(r(X,Y), 2*b(X,Y)) * gt(r(X,Y), 80), b(X,Y)*0.2, b(X,Y))' [recolored];
    [recolored] lutrgb=r='if(lt(val,25),0,val)':g='if(lt(val,25),0,val)':b='if(lt(val,25),0,val)',
                curves=m='0/0 0.12/0.3 0.4/0.8 0.7/0.95 1/1' [base];
    [base] split [a][b2];
    [b2] lutrgb=r='if(lt(val,35),0,val)':g='if(lt(val,35),0,val)':b='if(lt(val,35),0,val)',
         gblur=sigma=12 [glow];
    [a][glow] blend=all_mode=addition:all_opacity=0.55 [blended];
    [blended] lutrgb=r='if(lt(val,15),0,val)':g='if(lt(val,15),0,val)':b='if(lt(val,15),0,val)',
              format=yuv420p [out]
  " -map "[out]" -map 0:a -c:a copy \
  -c:v libx264 -crf 18 -preset medium -movflags +faststart \
  "output.mp4"
```

### Pipeline stages explained

| Stage | Filter | Purpose |
|-------|--------|---------|
| 1 | `format=gbrp` | Force planar RGB — avoids YUV chroma contamination that causes purple background |
| 2 | `drawbox` | Black rectangle over channel logo/watermark |
| 3 | `geq` (orange→green) | Per-pixel color replacement: orange sung text → bright green. Detection: R > 1.3*G AND R > 2*B AND R > 80 |
| 4 | `lutrgb` (threshold) | Zero out near-black RGB pixels (< 25) to ensure pure black background |
| 5 | `curves` | Brightness boost for text: aggressive S-curve that preserves black and lifts midtones |
| 6 | `split` + `gblur` + `blend` | Glow effect: blur a thresholded copy (bright pixels only), add back with 55% opacity |
| 7 | `lutrgb` (final cleanup) | Final pass to zero out any residual near-black pixels from the glow |
| 8 | `format=yuv420p` | Convert back to YUV for H.264 encoding |

### Key technical lessons learned

1. **YUV chroma contamination**: Using `eq=saturation` or `screen` blend in YUV space lifts black backgrounds to purple. Solution: force `format=gbrp` (planar RGB) for the entire filter chain, convert to YUV only at the very end.

2. **Glow without lifting blacks**: The `screen` blend mode always lifts dark pixels. Use `addition` blend instead, with a pre-thresholded glow source (lutrgb zeros near-black before blur).

3. **Orange→green color swap**: The `geq` filter allows cross-channel pixel access (r(X,Y), g(X,Y), b(X,Y)). Orange pixels are detected by ratio thresholds, then R and G channels are swapped/remapped.

4. **`unsharp` kernel limit**: ffmpeg's unsharp filter has a max kernel of 13x13 — too small for a visible bloom. The gblur+blend approach gives better control over glow radius.

## Logo mask presets (drawbox parameters)

| Channel | Position | drawbox parameters |
|---------|----------|--------------------|
| Musisi Karaoke | Bottom-left | `x=0:y=ih-300:w=330:h=300` |
| Sing King | TBD | TBD — needs analysis |
| Party Tyme | TBD | TBD — may not need processing (already uses white→green) |

## Color swap presets

| Source color | geq R formula | geq G formula | geq B formula | Notes |
|-------------|---------------|---------------|---------------|-------|
| Orange → Green | `b(X,Y)*0.2` | `clip(r(X,Y)*1.1, 0, 255)` | `b(X,Y)*0.2` | Tested on Musisi Karaoke. Detection: R>1.3G, R>2B, R>80 |
| Pink → Green | TBD | TBD | TBD | Needed for Sing King — uses thin pink/orange font |

## Performance notes

- The `geq` filter is very slow (~0.1x realtime on 1080p60 on Apple Silicon)
- A 4-minute song takes ~40 minutes to process
- **Future optimization ideas**:
  - Use `colorchannelmixer` or `hue` filter instead of `geq` (hardware-friendly)
  - Reduce to 30fps before processing if source is 60fps (halves work)
  - Use GPU acceleration (`-vf format=nv12,hwupload` + CUDA/VideoToolbox filters)
  - Pre-process with a faster tool (Python + OpenCV with NumPy vectorization)
  - Lower resolution during processing, upscale after
  - Use ffmpeg's `-threads` and `-filter_threads` options

## TODO

- [ ] Analyze Sing King karaoke videos (different font, pink/orange colors, thinner text)
- [ ] Build reusable processing script with channel presets
- [ ] Investigate performance optimizations for the geq bottleneck
- [ ] Test overlay blending result in Final Cut Pro
