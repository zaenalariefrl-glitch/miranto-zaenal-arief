#!/usr/bin/env bash
# QC: grab N evenly spaced frames into one image + waveform image of the audio
# Usage: tools/contact_sheet.sh out/opening/final.mp4 [N=12]
set -euo pipefail
IN="$1"; N="${2:-12}"; D="$(dirname "$IN")"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
FPS=$(python3 -c "print(max(0.01,$N/$DUR))")
ffmpeg -y -loglevel error -i "$IN" -vf "fps=$FPS,scale=480:-1,tile=4x$(( (N+3)/4 ))" -frames:v 1 "$D/contact.png"
ffmpeg -y -loglevel error -i "$IN" -filter_complex "showwavespic=s=1920x240:split_channels=1:colors=#d4af37|#b38b4d" -frames:v 1 "$D/wave.png"
echo "$D/contact.png  $D/wave.png"
