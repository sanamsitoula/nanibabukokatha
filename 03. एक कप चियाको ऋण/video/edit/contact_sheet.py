"""Build a labeled 3-column contact sheet from images: py -3 contact_sheet.py out.jpg img1 img2 ..."""
import subprocess
import sys
from pathlib import Path

COLS, W, H = 3, 640, 360


def main(out, images):
    args, filters, tags, layout = [], [], [], []
    for i, img in enumerate(images):
        args += ["-i", img]
        label = Path(img).stem
        filters.append(
            f"[{i}]scale={W}:{H},drawtext=text='{label}':fontcolor=yellow:fontsize=28:"
            f"box=1:boxcolor=black@0.6:x=8:y=8[v{i}]"
        )
        tags.append(f"[v{i}]")
        layout.append(f"{(i % COLS) * W}_{(i // COLS) * H}")
    graph = ";".join(filters) + ";" + "".join(tags) + f"xstack=inputs={len(images)}:layout={'|'.join(layout)}:fill=black"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", graph, "-frames:v", "1", "-q:v", "4", out], check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
