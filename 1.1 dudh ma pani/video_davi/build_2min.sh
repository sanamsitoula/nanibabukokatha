#!/usr/bin/env bash
# Builds the 2-minute cut: title card + one shot per scene (shot-selection.md) + moral card.
# Source clips in ../video are only read. Run from anywhere: bash build_2min.sh
set -euo pipefail
cd "$(dirname "$0")"

SRC=../video
OUT=dudh-ma-pani-2min.mp4
CARD_BG=0x8C2F39
TITLE_SECONDS=2.5
MORAL_SECONDS=5
SHOTS=(
  S1S4_202607231159 S2S1_202607231159 S3S4_202607231416 S4S3_202607262043
  S5S3_202607262020 S6S4_202607241202 S7S3---_202607241202 S8S4_202607262119
  S9S2_202607241201 S10S5_202607262015 S11S3_202607262014 S12S1_202607262035
)

inputs=()
for shot in "${SHOTS[@]}"; do
  [ -f "$SRC/$shot.mp4" ] || { echo "Missing source clip: $SRC/$shot.mp4" >&2; exit 1; }
  inputs+=(-i "$SRC/$shot.mp4")
done

card() {  # card <ass file> <seconds> <label>
  echo "color=c=$CARD_BG:s=1280x720:r=24:d=$2,ass=$1,format=yuv420p,setsar=1[v$3];anullsrc=r=48000:cl=stereo,atrim=duration=$2[a$3];"
}

graph="$(card title.ass "$TITLE_SECONDS" t)$(card moral.ass "$MORAL_SECONDS" m)"
chain="[vt][at]"
for i in "${!SHOTS[@]}"; do
  graph+="[$i:v]fps=24,scale=1280:720,format=yuv420p,setsar=1[v$i];[$i:a]aresample=48000,aformat=channel_layouts=stereo[a$i];"
  chain+="[v$i][a$i]"
done
graph+="${chain}[vm][am]concat=n=$(( ${#SHOTS[@]} + 2 )):v=1:a=1[v][a]"

ffmpeg -y -hide_banner -loglevel error "${inputs[@]}" -filter_complex "$graph" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "Built $OUT"
