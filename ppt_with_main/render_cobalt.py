"""Render Cobalt presentation chapters and concatenate to Cobalt.mp4."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

SCENES = [
    'C01_Chip', 'C02_OurProject', 'C03_Binary', 'C04_Ternary', 'C05_Quantum', 'C06_Neuromorphic',
    'C07_Compare', 'C08_TernaryUnits', 'C09_CurrentResearch', 'C10_BitNet', 'C11_Huawei', 'C12_TernaryStartup',
    'C13_GDDR7', 'C14_ProjectSplit', 'C15_Terbium', 'C16_TerbiumTools', 'C17_TerbiumInterface', 'C18_Cobalt',
    'C19_CobaltName', 'C20_CobaltSpecs', 'C21_CobaltInTerbium', 'C22_CobaltPhysical', 'C23_CobaltISA',
    'C24_ToolsUsed', 'C25_TechSpecs', 'C26_Limitations', 'C27_Credits1', 'C28_Credits2', 'C29_Questions', 'C30_ThankYou'
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality", choices=["l", "m", "h", "p", "k"], default="h")
    parser.add_argument("--slides", nargs="+", type=int, help="Scene numbers 1–30; default all")
    parser.add_argument("--concat", action="store_true", help="Join the selected clips after rendering")
    parser.add_argument("--concat-only", action="store_true", help="Join existing clips; do not rerender")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", default="Cobalt.mp4")
    parser.add_argument("--clip-dir", type=Path, help="Existing clip folder (with --concat-only)")
    args = parser.parse_args()

    total_scenes = len(SCENES)
    numbers = sorted(set(args.slides or range(1, total_scenes + 1)))
    if any(n < 1 or n > total_scenes for n in numbers):
        parser.error(f"Slide numbers must lie between 1 and {total_scenes}")
    if args.fps < 1:
        parser.error("fps must be positive")
    if args.clip_dir and not args.concat_only:
        parser.error("--clip-dir requires --concat-only")

    names = [SCENES[n - 1] for n in numbers]
    height = {"l": 480, "m": 720, "h": 1080, "p": 1440, "k": 2160}[args.quality]
    folder = ROOT / "media" / "videos" / "cobalt" / f"{height}p{args.fps}"
    if args.clip_dir:
        folder = args.clip_dir.resolve()

    if not args.concat_only:
        for name in names:
            print(f"Rendering {name}...", flush=True)
            subprocess.run([sys.executable, "-m", "manim", f"-q{args.quality}",
                            "--fps", str(args.fps), "cobalt.py", name], cwd=ROOT, check=True)

    if args.concat or args.concat_only:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise SystemExit("Install ffmpeg and add it to PATH to concatenate clips.")
        clips = [folder / f"{name}.mp4" for name in names]
        missing = [str(p) for p in clips if not p.is_file()]
        if missing:
            raise SystemExit("Missing rendered clips:\n" + "\n".join(missing))
        manifest = ROOT / "concat_cobalt.txt"
        def quote_path(path):
            return "'" + path.as_posix().replace("'", "'\\''") + "'"
        manifest.write_text("".join(f"file {quote_path(p)}\n" for p in clips), encoding="utf-8")
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(manifest),
                        "-c", "copy", "-movflags", "+faststart", args.output], cwd=ROOT, check=True)
        print(f"Successfully generated {ROOT / args.output}")

if __name__ == "__main__":
    main()
