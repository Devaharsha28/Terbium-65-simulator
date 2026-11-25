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

---

# Cobalt: Defense Presentation (30 Scenes)

Thirty independent Manim CE scenes built for the diploma project defense, with a minimal flat-dark aesthetic, large hall-readable typography, and uncluttered slides matching the reference storyboard from start to end.

- Source script: `cobalt.py`
- Batch renderer: `render_cobalt.py`
- Interactive HTML presenter: `presentation_cobalt.html`
- Output joined movie: `Cobalt.mp4`

## Scene Sequence (30 Scenes)

1. `C01_Chip`: Silicon chip layout (`chip_full.png`) with `RUBIDIUM / Ternary Computing System`
2. `C02_OurProject`: `Rubidium` with Government Institute of Electronics crest (`gioe_logo.png`), team members, guide, and diploma details
3. `C03_Binary`: `Binary` with digits `0    1`
4. `C04_Ternary`: `Ternary` with balanced digits `-1    0    +1`
5. `C05_Quantum`: `Quantum` with qubit notation `|0⟩`, `|1⟩`, `|ψ⟩`
6. `C06_Neuromorphic`: `Neuromorphic` with `Brain-based computing` and multi-layer neural network diagram
7. `C07_Compare`: `Different computing` 2x2 grid (`Binary`, `Ternary`, `Quantum`, `Neuromorphic`)
8. `C08_TernaryUnits`: `Units of ternary` (`trit`, `tryte`, `9 trits = 1 tryte`)
9. `C09_CurrentResearch`: `Current research`
10. `C10_BitNet`: `Microsoft BitNet` (`bitnet.png` and `network_diagram.png` side by side)
11. `C11_Huawei`: `Huawei` (`huawei.png` with `Ternary logic gate patent / CN119652311A / Filed September 2023`)
12. `C12_TernaryStartup`: `Tern Computing` (`startup.png` wave logo)
13. `C13_GDDR7`: `GDDR7` (`nvidia_5090.png` + `memory_makers.png` + `RTX 5090 GPU` + `GDDR7 uses PAM3 signalling: 3 voltage levels`)
14. `C14_ProjectSplit`: `Our project` with `Terbium` | `Cobalt`
15. `C15_Terbium`: `Terbium` (`Ternary circuit simulator`)
16. `C16_TerbiumTools`: `Terbium tools` (`unity_logo.png` + `Unity`, `csharp_logo.png` + `C#`)
17. `C17_TerbiumInterface`: `Terbium interface` (`terbium_ui.png`)
18. `C18_Cobalt`: `Cobalt R309B1` (`Ternary CPU`)
19. `C19_CobaltName`: `Cobalt R309B1: the name` (Heptavintimal, Radix 3, 9 trits, Batch 1 breakdown)
20. `C20_CobaltSpecs`: `Cobalt in Terbium: specifications` (Harvard architecture, 9 trits, ROM: 19683 x 9, 27 registers, RAM: 27 locations)
21. `C21_CobaltInTerbium`: `Cobalt in Terbium` (`cobalt_in_terbium.png`)
22. `C22_CobaltPhysical`: `Cobalt physical` (`cobalt_chip.png` with `Cobalt layout`)
23. `C23_CobaltISA`: `Cobalt: stripped down (ISA)` (9 instructions table: HLT, ADD, SUB, MIN, MAX, MUL, MOV, LDA, LDB + format `[ opcode (8 bits) | immediate (10 bits) ]`)
24. `C24_ToolsUsed`: `Tools used` (`Yosys`, `OpenROAD`, `SkyWater 130nm PDK`)
25. `C25_TechSpecs`: `Cobalt layout: specifications` (40 kHz, 7,840 transistors, 1.8 V, 18-bit instruction, 2 registers, 16-instruction memory, 2 cycles / instruction)
26. `C26_Limitations`: `Limitations` (No physical chip, No wide software, Heat issues, Noise)
27. `C27_Credits1`: `Credits` (Sebastian Lague, louis-dr)
28. `C28_Credits2`: `Credits` (Douglas W. Jones, Setun)
29. `C29_Questions`: `Questions?`
30. `C30_ThankYou`: `Thank you`

## Rendering Cobalt

Render all 30 scenes and concatenate to `Cobalt.mp4`:
```bash
./.venv_linux/bin/python render_cobalt.py --quality h --fps 30 --concat
```

Or preview specific scenes:
```bash
./.venv_linux/bin/python render_cobalt.py --slides 1 2 3 4 5 --quality l
```
