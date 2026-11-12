"""Render selected independent chapters and concatenate in presentation order."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
# Deliberately independent of importing Manim, for --help and setup troubleshooting.
SCENES = ["Slide01Rubidium", "Slide02Trit", "Slide03InsideRubidium", "Slide04Progress",
          "Slide05HowTerbiumWasMade", "Slide06WorkingSimulator", "Slide07CircuitsBuilt",
          "Slide08SpecialCircuit", "Slide09NeuronMath", "Slide10MathToHardware", "Slide11OurNeuron",
          "Slide12NeuronToNetwork", "Slide13Verification", "Slide14NextCobalt", "Slide15ThankYou"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality", choices=["l", "m", "h", "p", "k"], default="h")
    parser.add_argument("--slides", nargs="+", type=int, help="Scene numbers 1–15; default all")
    parser.add_argument("--concat", action="store_true", help="Join the selected clips after rendering")
    parser.add_argument("--concat-only", action="store_true", help="Join existing clips; do not rerender")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", default="Rubidium.mp4")
    parser.add_argument("--clip-dir", type=Path, help="Existing clip folder (with --concat-only)")
    args = parser.parse_args()
    numbers = sorted(set(args.slides or range(1, 16)))
    if any(n < 1 or n > 15 for n in numbers):
        parser.error("Slide numbers must lie between 1 and 15")
    if args.fps < 1:
        parser.error("fps must be positive")
    if args.clip_dir and not args.concat_only:
        parser.error("--clip-dir requires --concat-only")
    names = [SCENES[n - 1] for n in numbers]
    height = {"l": 480, "m": 720, "h": 1080, "p": 1440, "k": 2160}[args.quality]
    folder = ROOT / "media" / "videos" / "rubidium" / f"{height}p{args.fps}"
    if args.clip_dir:
        folder = args.clip_dir.resolve()
    if not args.concat_only:
        for name in names:
            print(f"Rendering {name}", flush=True)
            subprocess.run([sys.executable, "-m", "manim", f"-q{args.quality}",
                            "--fps", str(args.fps), "rubidium.py", name], cwd=ROOT, check=True)
    if args.concat or args.concat_only:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise SystemExit("Install ffmpeg and add it to PATH to concatenate clips.")
        clips = [folder / f"{name}.mp4" for name in names]
        missing = [str(p) for p in clips if not p.is_file()]
        if missing:
            raise SystemExit("Missing rendered clips:\n" + "\n".join(missing))
        manifest = ROOT / "concat.txt"
        # FFmpeg concat demuxer quoting, including paths containing apostrophes.
        def quote_path(path):
            return "'" + path.as_posix().replace("'", "'\\''") + "'"
        manifest.write_text("".join(f"file {quote_path(p)}\n" for p in clips), encoding="utf-8")
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(manifest),
                        "-c", "copy", "-movflags", "+faststart", args.output], cwd=ROOT, check=True)
        print(f"Created {ROOT / args.output}")


if __name__ == "__main__":
    main()
