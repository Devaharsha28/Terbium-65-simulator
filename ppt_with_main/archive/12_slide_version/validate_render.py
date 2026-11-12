"""Render all scenes, capture narration beats, and audit safe-area bounds.

This makes full-duration, silent 640×360 / 8 fps review clips. It does not
change the 1080p defaults in manim.cfg. Run with the project Python.
"""
from pathlib import Path
import json
import sys
from manim import tempconfig
import rubidium as deck

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "review"
OUT.mkdir(exist_ok=True)
records = []
issues = []
original_pause = deck.Chapter.pause
original_finish = deck.Chapter.finish


def capture(scene):
    count = sum(r["scene"] == type(scene).__name__ for r in records)
    scene.renderer.update_frame(scene)
    target = OUT / f"{type(scene).__name__}_{count:02d}.png"
    scene.renderer.camera.get_image().save(target)
    records.append({"scene": type(scene).__name__, "time": round(scene.time, 2), "image": target.name})
    for m in scene.mobjects:
        if m.width and m.height and (m.get_left()[0] < -6.9 or m.get_right()[0] > 6.9
                                    or m.get_bottom()[1] < -3.85 or m.get_top()[1] > 3.85):
            issues.append({"scene": type(scene).__name__, "time": scene.time,
                           "object": type(m).__name__, "bounds": [float(m.get_left()[0]), float(m.get_right()[0]),
                                                                     float(m.get_bottom()[1]), float(m.get_top()[1])]})


def review_pause(self, seconds=deck.HOLD):
    original_pause(self, seconds)
    capture(self)


def review_finish(self):
    capture(self)
    original_finish(self)


def main():
    # Unknown data must never produce a pass; a measured consistent case may.
    assert deck.verification_data() == (None, False, False)
    old = [deck.TEST_INPUTS, deck.TEST_WEIGHTS, deck.TEST_BIAS, deck.EXPECTED_OUTPUT, deck.TERBIUM_OUTPUT]
    deck.TEST_INPUTS, deck.TEST_WEIGHTS, deck.TEST_BIAS = [1, 0, -1], [1, -1, 1], 1
    deck.EXPECTED_OUTPUT = deck.TERBIUM_OUTPUT = 1
    assert deck.verification_data() == (1, True, True)
    deck.TERBIUM_OUTPUT = 0
    assert not deck.verification_data()[2]
    deck.EXPECTED_OUTPUT = deck.TERBIUM_OUTPUT = 2
    assert not deck.verification_data()[2]  # internally inconsistent values
    deck.TEST_INPUTS, deck.TEST_WEIGHTS, deck.TEST_BIAS, deck.EXPECTED_OUTPUT, deck.TERBIUM_OUTPUT = old
    snapshot_only = "--snapshots-only" in sys.argv
    with tempconfig({"pixel_width": 640, "pixel_height": 360, "frame_rate": 8,
                     "media_dir": str(ROOT / "media_review"), "disable_caching": True,
                     "save_last_frame": snapshot_only, "write_to_movie": not snapshot_only,
                     "progress_bar": "none", "verbosity": "WARNING"}):
        # Asset fallback even when a screenshot is missing.
        missing = deck.screenshot_frame("assets/__missing__.png", "Missing asset test")
        assert len(missing) == 3
        deck.Chapter.pause = review_pause
        deck.Chapter.finish = review_finish
        for name in deck.SCENE_NAMES:
            print(f"REVIEW {name}", flush=True)
            # File-writer configuration is mutable; isolate output per chapter.
            with tempconfig({"output_file": name}):
                scene = getattr(deck, name)()
                scene.render()
            records.append({"scene": name, "duration": round(scene.time, 2)})
    (OUT / "validation.json").write_text(json.dumps({"records": records, "safe_area_issues": issues}, indent=2), encoding="utf-8")
    # Compact contact sheets preserve every captured beat for visual inspection.
    from PIL import Image, ImageDraw
    for name in deck.SCENE_NAMES:
        files = sorted(OUT.glob(f"{name}_*.png"))
        if not files:
            continue
        sheet = Image.new("RGB", (960, 200 * ((len(files) + 2) // 3)), "#0B111D")
        draw = ImageDraw.Draw(sheet)
        for i, path in enumerate(files):
            im = Image.open(path).convert("RGB").resize((320, 180))
            x, y = (i % 3) * 320, (i // 3) * 200
            sheet.paste(im, (x, y))
            draw.text((x + 5, y + 181), path.stem, fill="white")
        sheet.save(OUT / f"{name}_contact.jpg")
    print(f"Safe-area issues: {len(issues)}", flush=True)
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
