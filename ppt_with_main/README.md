# Rubidium

Fifteen independent Manim scenes on a 16:9 engineering canvas. Silent animation,
1920 × 1080 at 30 fps. Each scene ends with a stable composition held for
1.6–2 seconds; the simulator QR stays visible for 2.5 seconds.

The editable source is `rubidium.py`. The joined presentation is `Rubidium.mp4`.
Individual scenes are in `media/videos/rubidium/1080p30/`.
The earlier twelve-scene source is preserved in `archive/before_15_scenes/`.

## Scene sequence

1. Rubidium: balanced ternary states and minimal cover
2. Trit: quick binary recap, three discrete states, classical versus quantum
3. Inside Rubidium: Terbium and Cobalt project branches
4. Progress: Terbium v1 completed, writable memory remains unresolved
5. How Terbium was made: Unity, C#, editor capabilities, actual interface
6. Working simulator: large interface, sequential callouts, exact GitHub QR
7. Circuits built: 3:1, 9:1, 27:1 MUX and 1:3, 1:9, 1:27 DEMUX
8. Special circuit: ternary neural network, feed-forward inference
9. Neuron mathematics: inputs, weights, products, sum, bias, activation
10. Math to hardware: operations become circuit blocks
11. Our neuron: sequential highlights on the supplied circuit screenshot
12. Neuron to network: abstract 3 → 3 → 1, then actual network screenshot
13. Verification: 25 cells, 24 matches, 1 incorrect output, 96% over these tests
14. Next Cobalt: writable memory, architecture implementation, ternary computer
15. Thank you: opening composition returns

## Supplied assets

The supplied files were copied without renaming or modifying their contents:

- `terbium ui.png`
- `27mux.png`
- `27demux.png`
- `neuron.png`
- `network.png`
- `terbium-tRsAWc.png` (exact GitHub QR)
- `download.png` (Unity logo)

The existing real `mux3.png`, `mux9.png`, `demux3.png`, and `demux9.png`
screenshots supply the smaller routing stages. Their circuit labels and
structures were checked visually. The simulator calls the larger MUX circuits
“9-2 mux” and “27-3 mux”; the presentation uses the requested data-routing
ratios 9:1 and 27:1.

All images retain their aspect ratio. Missing or unreadable images display a
styled placeholder. The QR retains its exact square source, colors and
orientation. An additional black margin surrounds the source image, outside
its pixels. At 1080p, the QR image occupies approximately 418 pixels square.
The QR is only in Scene 6.

## Content boundaries

The measured comparison is the user-supplied result: 24 of 25 circuit outputs
matched the mathematical reference. The red grid cell's location is illustrative,
since no per-test ordering was supplied. It does not claim universal ANN accuracy.
The sample propagating signals illustrate inference flow rather than a numerical
test case. There is no training animation or claim of training in the circuit.

The neuron maps the multi-trit adder result into the ternary domain and is labeled
“activation / ternary quantization.” No ordinary ReLU transfer function is asserted.
Cobalt remains conceptual pending a practical writable ternary memory element.
No unmeasured precision improvement is claimed.

## Render

Use the existing project-local Python 3.10 environment:

```powershell
.\.venv310\Scripts\python.exe render_all.py --quality h --fps 30 --concat
```

Render selected scenes:

```powershell
.\.venv310\Scripts\python.exe render_all.py --slides 9 10 11 --quality h
```

Preview a single scene:

```powershell
.\.venv310\Scripts\python.exe -m manim -ql rubidium.py Slide09NeuronMath
```

`requirements.txt` pins Manim CE 0.19.0. The source uses Segoe UI and Cambria
Unicode mathematics, so no LaTeX installation is needed. FFmpeg is required
for joining clips. It is available at `D:\ffmpeg\bin\ffmpeg.exe` here.

`RUBIDIUM_PACE` scales animation and hold durations for drafting. Leave it unset
for final output. Colors and asset mappings are at the top of `rubidium.py`.
Screenshot highlights use normalized coordinates tied to the supplied images.

## Visual review

```powershell
.\.venv310\Scripts\python.exe validate_render.py --snapshots-only
```

This captures each stable beat, builds contact sheets in `review15/`, and checks
screen bounds. Omit `--snapshots-only` to render complete 960 × 540 / 10 fps
review animations. The final movie uses the separate 1080p rendering path.

For live presenting, open `presentation.html` in a browser. Click Play, then use
the left/right arrow keys to change scenes, Space to pause, R to replay, or F for
fullscreen. Each scene stays on its final frame until you advance. Controls hide
while presenting. Keep this file next to the `media` directory.

You can also play the joined movie directly. The movie has no narration or music.
