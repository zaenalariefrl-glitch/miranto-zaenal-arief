#!/usr/bin/env bash
# One-shot pipeline: scene.html -> out/<name>/final.mp4 (60fps video + mixed SFX, -14 LUFS)
# Usage: tools/make_video.sh scenes/opening.html [--fps 60] [--workers 4] [--from s --to s] [--scale 1]
#        AUDIO_ONLY=1 tools/make_video.sh scenes/opening.html   # re-mix sound without re-rendering
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCENE="$1"; shift
NAME="$(basename "${SCENE%.*}")"
OUT="$HERE/../out/$NAME"; mkdir -p "$OUT"
if [ "${AUDIO_ONLY:-0}" != "1" ]; then node "$HERE/render.mjs" "$SCENE" "$OUT" "$@"; fi
python3 "$HERE/sfx.py" mix "$OUT/cues.json" "$OUT/sfx.wav"
ffmpeg -y -loglevel error -i "$OUT/video.mp4" -i "$OUT/sfx.wav" \
  -filter_complex "[1:a]loudnorm=I=-14:TP=-1.0:LRA=11[a]" -map 0:v -map "[a]" \
  -c:v copy -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$OUT/final.mp4"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate -show_entries format=duration -of compact "$OUT/final.mp4"
echo "-> $OUT/final.mp4"
