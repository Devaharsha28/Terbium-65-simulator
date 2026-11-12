# RUBIDIUM — A Ternary Computing Ecosystem

A silent Manim CE presentation, with twelve independently editable scenes.
Default target: **1920×1080, 30 fps, 16:9**. Planned duration: **8 minutes**.
Your supplied screenshots are already copied into `assets/`; originals are untouched.

## Files

```text
ppt_with_main/
  rubidium.py             complete source, configuration and twelve chapters
  render_all.py           ordered rendering and optional MP4 concatenation
  validate_render.py      full-duration draft renders and safe-area audit
  requirements.txt        manim==0.19.0
  manim.cfg               1080p / 30 fps / Cairo defaults
  assets/
    terbium_main.png      supplied activation screen used as interface example
    mux3.png              Screenshot ...214651
    demux3.png            Screenshot ...214658
    mux9.png              Screenshot ...214706 (UI calls it "9-2 mux")
    demux9.png            Screenshot ...214726
    mux27.png             Screenshot ...214719 (UI calls it "27-3 mux")
    demux27.png           Screenshot ...214732
    adder.png             Screenshot ...214600
    activation.png        Screenshot ...214618
    neuron.png            Screenshot ...214552
    network.png           Screenshot ...214637
  review/                 rendered narration-beat images and validation report
  media_review/            full-duration draft chapter videos
  media/                  normal render output, created by Manim
  Rubidium_preview.mp4    joined 640×360 / 8 fps draft, with full narration pauses
```

The 9:1 and 27:1 presentation labels describe data inputs to one output;
the simulator's names apparently indicate selector counts (2 and 3).
Screenshots are evidence of circuit structure, not complete truth-table tests.
The unused `adder` and `activation` asset constants are available for later editing.

## Install (Windows / PowerShell)

Use Python **3.10–3.12** for this pinned release. In this workspace the existing
Python 3.10 interpreter is at `C:\Users\Deva\AppData\Local\Programs\Python\Python310\python.exe`.
Python 3.14 encountered missing prebuilt ModernGL/glcontext wheels; changing
Python avoids requiring a C++ compiler. No extra Python packages beyond Manim
and its automatically installed dependencies are needed.

```powershell
# Standard new setup, using a Python 3.10–3.12 interpreter:
python -m venv .venv310
.\.venv310\Scripts\python.exe -m pip install -r requirements.txt
```

The project-local `.venv310` environment is used for validation. Activation is
optional because all commands below use its interpreter directly.
If a managed environment cannot bootstrap pip, an existing modern pip can target
it with `python -m pip --python .\.venv310\Scripts\python.exe install -r requirements.txt`.

Equations automatically use `MathTex` if `latex` and `dvisvgm` are on PATH.
Otherwise the presentation uses readable Cambria Unicode formulas with no TeX
dependency. For full mathematical typesetting install MiKTeX (including the
`standalone`, `preview`, and `amsmath` packages and dvisvgm), then restart the shell.
Manim's official [installation guide](https://docs.manim.community/en/stable/installation/uv.html)
and [text guide](https://docs.manim.community/en/stable/guides/using_text.html)
explain the distinction between Pango text and TeX equations.

```powershell
$env:RUBIDIUM_MATH = 'text'  # optional: force portable mode
# 'auto' is the default; 'latex' requires the TeX toolchain and reports errors.
```

FFmpeg is needed only by the concatenation script. It is already available on
this machine at `D:\ffmpeg\bin\ffmpeg.exe`; on another machine add ffmpeg to PATH.

## Render one chapter

Low-quality test (480p; retain narration pauses):

```powershell
.\.venv310\Scripts\python.exe -m manim -ql rubidium.py Slide01Title
```

1080p / 30 fps:

```powershell
.\.venv310\Scripts\python.exe -m manim -qh --fps 30 rubidium.py Slide09BuildingTernaryNeuron
```

Quick animation-only test with shortened pauses (reset before final output):

```powershell
$env:RUBIDIUM_PACE = '0.2'
.\.venv310\Scripts\python.exe -m manim -ql rubidium.py Slide08LogicToNeuron
Remove-Item Env:RUBIDIUM_PACE
```

## Render all and join

```powershell
.\.venv310\Scripts\python.exe render_all.py --quality h --concat
```

This renders twelve clips in order and writes `Rubidium.mp4`. It uses separate
processes so each chapter can be changed and rerendered independently.
To update only chapters 8 and 9, then join all existing chapters:

```powershell
.\.venv310\Scripts\python.exe render_all.py --quality h --slides 8 9
.\.venv310\Scripts\python.exe render_all.py --quality h --concat-only
```

All clips must use the same quality and fps. The generated `concat.txt` contains
the ordered absolute clip paths. The equivalent direct FFmpeg command is:

```powershell
ffmpeg -y -f concat -safe 0 -i concat.txt -c copy -movflags +faststart Rubidium.mp4
```

No audio or narration is generated. Each chapter ends with a short fade to black.

To recreate the bundled draft from its rendered chapters:

```powershell
.\.venv310\Scripts\python.exe render_all.py --concat-only --clip-dir media_review/videos/360p8 --output Rubidium_preview.mp4
```

## Editing

Colors, fonts, animation timing, chapter durations, screenshot paths, and test
values are at the top of `rubidium.py`. Find a `SCENE NN` comment to edit one chapter.
Every required helper is shared; screenshot frames preserve aspect ratio and
fall back safely for missing/unreadable files. Paths resolve relative to the source.

Set `TEST_INPUTS` and `TEST_WEIGHTS` to lists of three numbers, `TEST_BIAS` to a
number, and `EXPECTED_OUTPUT` / `TERBIUM_OUTPUT` to your actual measured scalar
results. Defaults are `None`: symbolic unknown values and **no pass check**.
The pass check requires equal finite numeric outputs, and when inputs/weights/bias
are supplied it also checks the direct mathematical result. Exact equality is
intentional for integer ternary arithmetic. The three-value test models the
three-input neuron, not a full multi-layer network test or overflow emulation.

"Arithmetic/inference path verified" is explicitly attributed to your supplied
project report. It does not imply that unknown configured data were verified.
The network remains a proof of concept. Cobalt remains in progress.

For balanced integer ternary with T trits, the maximum magnitude is `(3**T-1)/2`.
An exact product range uses `RₓR_w`; the conservative accumulation range uses
`N RₓR_w + |b|max`. Choose the smallest output width T with `(3**T-1)/2` at least
that range. The displayed `Tp ≈ Tx+Tw` and `Tacc ≈ Tp+ceil(log₃N)` are safe
engineering estimates for integer products and accumulation before bias; bias,
fractional scaling, saturation and intermediate implementation widths require
separate range checks. The graph in scene 8 illustrates the ideal `max(0,z)`;
the finite ternary implementation is described as quantized/ReLU-like.

## Scene names

1. `Slide01Title`
2. `Slide02TernaryRecap`
3. `Slide03ProposalToImplementation`
4. `Slide04Terbium65`
5. `Slide05BuildingTernaryLogic`
6. `Slide06PowersOfThree`
7. `Slide07CobaltMemory`
8. `Slide08LogicToNeuron`
9. `Slide09BuildingTernaryNeuron`
10. `Slide10NeuronToNetwork`
11. `Slide11Verification`
12. `Slide12Conclusion`

## Compatibility and checks

- Use **Manim Community Edition**, not manimlib. The requirements pin 0.19.0.
- A TeX compilation error: use `RUBIDIUM_MATH=text`, or repair MiKTeX packages/PATH.
- Missing font/glyphs: edit `FONT`, `MATH_FONT`, `MONO_FONT`; on Linux use
  DejaVu Sans / DejaVu Serif / DejaVu Sans Mono. Recheck Unicode formulas.
- Images belong in `Group`, not `VGroup`; the framing helper handles this.
- A modified clip does not appear: rerender it with `--disable_caching`.
- Joining fails: check ffmpeg PATH and matching clip resolution/fps.
- Run `.\.venv310\Scripts\python.exe validate_render.py` to render all chapters,
  capture beats, inspect safe-area bounds and test verification/fallback behavior.
  View `review/*_contact.jpg` to review layout, and `review/validation.json` for durations.
- The portable text math path is validated separately from optional MathTex;
  the latter requires your local TeX installation for an actual render check.

## Validation completed in this workspace

All twelve chapters rendered with Manim CE 0.19.0 at 640×360 / 8 fps. Their
joined preview is 480.000 seconds with a video-only stream. Captured narration
beats were visually reviewed; the safe-area audit reports zero issues. Unknown,
matching, mismatching and internally inconsistent verification cases and the
missing-image fallback were checked. The title also rendered at 1920×1080 / 30 fps
through `render_all.py`. Optional LaTeX rendering has not been tested here.
