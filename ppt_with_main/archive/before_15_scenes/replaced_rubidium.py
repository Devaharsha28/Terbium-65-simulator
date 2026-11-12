"""RUBIDIUM — twelve independent Manim Community Edition chapters.

Render: python -m manim -ql rubidium.py Slide01Title
All:    python render_all.py --quality h --concat
No audio is generated. All experimental values default to unknown.
"""
from pathlib import Path
import math
import os
import shutil
import warnings

from manim import *

# ========================= EDITABLE CONFIGURATION =========================
ROOT = Path(__file__).resolve().parent
BG = "#0B111D"
INK = "#E8EDF3"
MUTED = "#96A4B7"
NEG = "#EF7972"
ZERO = "#99A4B2"
POS = "#60BDEC"
GOLD = "#EBC76A"
COBALT = "#A79BD5"
PANEL = "#141F30"
FONT = "Segoe UI"
MATH_FONT = "Cambria"
MONO_FONT = "Consolas"
ANIM = 0.8
HOLD = 3.0
# 480 seconds including transitions, with room for live narration.
CHAPTER_SECONDS = [22, 38, 34, 36, 43, 49, 44, 46, 45, 45, 40, 38]
PACE = float(os.getenv("RUBIDIUM_PACE", "1"))
# auto uses MathTex only when both LaTeX and dvisvgm are installed.
# Set RUBIDIUM_MATH=latex to require LaTeX; text to force the portable fallback.
MATH_MODE = os.getenv("RUBIDIUM_MATH", "auto")
ASSETS = {key: f"assets/{key}.png" for key in (
    "terbium_main", "mux3", "demux3", "mux9", "demux9", "mux27",
    "demux27", "adder", "activation", "neuron", "network")}
TERBIUM_MAIN_IMAGE = ASSETS["terbium_main"]
NEURON_IMAGE = ASSETS["neuron"]
NETWORK_IMAGE = ASSETS["network"]

# Use measured data only. Three inputs, three weights, scalar bias/output.
# None deliberately keeps the comparison symbolic and displays no check mark.
TEST_INPUTS = None
TEST_WEIGHTS = None
TEST_BIAS = None
EXPECTED_OUTPUT = None
TERBIUM_OUTPUT = None

config.background_color = BG
config.frame_width = 14.2222222222
config.frame_height = 8
# Resolution/fps are in manim.cfg, so CLI -ql/-qh overrides stay effective.

# ============================== HELPERS ==================================
def label(text, size=28, color=INK, width=None, font=FONT):
    mob = Text(text, font=font, font_size=size, color=color, line_spacing=0.8)
    if width is not None and mob.width > width:
        mob.scale_to_fit_width(width)
    return mob


def equation(tex, plain, size=36, width=12):
    """Explicit Unicode alternative keeps every equation runnable without TeX."""
    use_tex = MATH_MODE == "latex" or (
        MATH_MODE == "auto" and shutil.which("latex") and shutil.which("dvisvgm"))
    mob = MathTex(tex, font_size=size, color=INK) if use_tex else label(
        plain, size, font=MATH_FONT)
    if mob.width > width:
        mob.scale_to_fit_width(width)
    return mob


def title(text, index):
    heading = label(text, 35, width=12.5).move_to([0, 3.23, 0])
    number = label(f"{index:02d} / 12", 15, MUTED).move_to([6, 3.7, 0])
    rule = Line([-6.35, 2.78, 0], [6.35, 2.78, 0], color=PANEL)
    return VGroup(heading, rule, number)


def trit(value, radius=0.36):
    color = {-1: NEG, 0: ZERO, 1: POS}[value]
    symbol = {-1: "−1", 0: "0", 1: "+1"}[value]
    circle = Circle(radius, color=color, fill_color=color, fill_opacity=0.14)
    return VGroup(circle, label(symbol, 26, color).move_to(circle))


def circuit_block(text, width=1.6, height=0.85, color=POS):
    box = RoundedRectangle(width=width, height=height, corner_radius=0.09,
                           color=color, stroke_width=2, fill_color=PANEL,
                           fill_opacity=1)
    caption = label(text, 23, width=width - 0.18, font=MONO_FONT).move_to(box)
    if caption.height > height - 0.16:
        caption.scale_to_fit_height(height - 0.16)
    return VGroup(box, caption)


def wire(start, end, color=MUTED, elbow=False):
    a = start.get_right() if isinstance(start, Mobject) else np.array(start)
    b = end.get_left() if isinstance(end, Mobject) else np.array(end)
    if elbow:
        mid = (a[0] + b[0]) / 2
        return VMobject(color=color, stroke_width=2.5).set_points_as_corners(
            [a, [mid, a[1], 0], [mid, b[1], 0], b]).set_z_index(-1)
    return Line(a, b, color=color, stroke_width=2.5).set_z_index(-1)


def neuron(name="", radius=0.43, color=POS):
    circle = Circle(radius, color=color, fill_color=PANEL, fill_opacity=1)
    return VGroup(circle, label(name, 24, color).move_to(circle)) if name else VGroup(circle)


def network_connections(left, right, color=MUTED):
    return VGroup(*(wire(a, b, color) for a in left for b in right))


def status(text, color=POS):
    dot = Dot(radius=0.065, color=color)
    return VGroup(dot, label(text, 21, color)).arrange(RIGHT, buff=0.15)


def section_transition(scene, text):
    cue = label(text, 30, GOLD, width=12).move_to([0, -2.95, 0])
    scene.reveal(cue)
    scene.pause(2)
    scene.play(FadeOut(cue), run_time=ANIM)


def screenshot_frame(path, caption, width=11.4, height=4.7):
    """Group (not VGroup): ImageMobject is not a vector mobject.

    Aspect-fit inside a dark frame; never stretch, never crop away circuitry.
    Missing/unreadable files have an intentionally useful placeholder.
    """
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    border = RoundedRectangle(width=width, height=height, corner_radius=0.1,
                              color=MUTED, stroke_width=1.2,
                              fill_color=PANEL, fill_opacity=1)
    content = None
    if resolved.is_file():
        try:
            content = ImageMobject(str(resolved))
            content.scale(min((width - 0.2) / content.width,
                              (height - 0.2) / content.height))
        except (OSError, ValueError) as exc:
            warnings.warn(f"Cannot read screenshot {resolved}: {exc}")
    if content is None:
        content = VGroup(label(caption, 25, MUTED, width=width - 0.6),
                         label("Add the image in assets/", 17, MUTED)).arrange(DOWN, buff=0.35)
    content.move_to(border)
    caption_mob = label(caption, 18, MUTED, width=width).next_to(border, DOWN, buff=0.14)
    return Group(border, content, caption_mob)


def routing_tree(depth, reverse=False):
    """A full ternary hierarchy: 3^depth leaves, 3 children per internal node."""
    levels, edges = [], VGroup()
    for level in range(depth + 1):
        count = 3 ** level
        x = -4.9 + 9.8 * level / depth
        if reverse:
            x = -x
        nodes = VGroup(*(Dot([x, (2.2 - 4.4 * i / (count - 1)) if count > 1 else 0, 0],
                            radius=0.045 if count > 9 else 0.07,
                            color=POS) for i in range(count)))
        levels.append(nodes)
        if level:
            for i, node in enumerate(nodes):
                parent = levels[level - 1][i // 3]
                edges.add(Line(parent.get_center(), node.get_center(),
                               color=MUTED, stroke_width=1.5).set_z_index(-1))
    return VGroup(edges, *levels)


def neuron_architecture():
    inputs = VGroup(*(equation(f"x_{i}", f"x{i}", 30).move_to([-5.8, y, 0])
                      for i, y in zip(range(1, 4), [1.1, 0, -1.1])))
    muls = VGroup(*(circuit_block(f"MUL w{i}", 1.55).move_to([-3.75, y, 0])
                    for i, y in zip(range(1, 4), [1.1, 0, -1.1])))
    accum = circuit_block("ADD", 1.55, 1.65).move_to([-0.85, 0, 0])
    bias = circuit_block("+ b", 1.2, color=GOLD).move_to([1.3, 0, 0])
    activation = circuit_block("f(z)", 1.4, color=GOLD).move_to([3.25, 0, 0])
    output = equation("y", "y", 36).move_to([5.4, 0, 0])
    links = VGroup(*(wire(a, b) for a, b in zip(inputs, muls)),
                   *(wire(a, accum, elbow=True) for a in muls),
                   wire(accum, bias), wire(bias, activation), wire(activation, output))
    return VGroup(links, inputs, muls, accum, bias, activation, output)


class Chapter(Scene):
    """Consistent pacing and a safe content area; each subclass is standalone."""
    chapter_index = 1

    def setup(self):
        super().setup()
        self.camera.background_color = BG
        self.started_at = self.time

    def play(self, *animations, **kwargs):
        # Scene.wait calls play(Wait(...)); preserve its already-scaled duration.
        # Overriding Wait with the generic animation timing would erase pauses.
        if len(animations) == 1 and isinstance(animations[0], Wait):
            return super().play(*animations, **kwargs)
        kwargs["run_time"] = kwargs.get("run_time", ANIM) * PACE
        return super().play(*animations, **kwargs)

    def pause(self, seconds=HOLD):
        self.wait(seconds * PACE)

    def reveal(self, *mobs):
        self.play(LaggedStart(*(FadeIn(m, shift=UP * 0.12) for m in mobs), lag_ratio=0.12))

    def begin(self, text):
        self.header = title(text, self.chapter_index)
        self.reveal(self.header)

    def clear_body(self):
        body = [m for m in self.mobjects if m is not getattr(self, "header", None)]
        if body:
            self.play(*(FadeOut(m) for m in body))

    def finish(self):
        target = CHAPTER_SECONDS[self.chapter_index - 1] * PACE
        remaining = target - (self.time - self.started_at) - ANIM * PACE
        if remaining > 0:
            self.wait(remaining)
        self.play(*(FadeOut(m) for m in list(self.mobjects)))


# ======================= SCENE 01 — RUBIDIUM ==============================
class Slide01Title(Chapter):
    chapter_index = 1

    def construct(self):
        name = label("RUBIDIUM", 74).move_to([0, 0.95, 0])
        subtitle = label("A Ternary Computing Ecosystem", 28, MUTED).move_to([0, -0.05, 0])
        states = VGroup(*(trit(v, 0.44) for v in [-1, 0, 1])).arrange(RIGHT, buff=1.1)
        states.move_to([0, -1.5, 0])
        self.play(Write(name), run_time=1.5)
        self.reveal(subtitle)
        self.pause(2)
        self.reveal(*states)
        self.finish()


# ======================= SCENE 02 — RECAP =================================
class Slide02TernaryRecap(Chapter):
    chapter_index = 2

    def construct(self):
        self.begin("Ternary: a quick recap")
        recap = label("From our first presentation", 20, MUTED).move_to([0, 2.35, 0])
        binary = VGroup(label("Binary", 25, MUTED), equation(r"\{0,1\}", "{0, 1}", 42)).arrange(DOWN)
        ternary = VGroup(label("Balanced ternary", 25, POS),
                        VGroup(*(trit(v) for v in [-1, 0, 1])).arrange(RIGHT, buff=0.5)).arrange(DOWN)
        binary.move_to([-3.1, 0.7, 0]); ternary.move_to([2.8, 0.7, 0])
        self.reveal(recap, binary, ternary)
        self.pause(6)
        self.clear_body()
        digits = VGroup(*(trit(v, 0.5) for v in [1, 0, -1])).arrange(RIGHT, buff=1.3).move_to([0, 1.35, 0])
        powers = VGroup(*(equation(t, p, 28).next_to(d, DOWN, buff=0.3)
                          for d, t, p in zip(digits, [r"3^2=9", r"3^1=3", r"3^0=1"],
                                            ["3² = 9", "3¹ = 3", "3⁰ = 1"])))
        self.reveal(digits, powers)
        self.pause(4)
        expansion = equation(r"(+1)\times9+0\times3+(-1)\times1", "(+1) × 9 + 0 × 3 + (−1) × 1", 40).move_to([0, -0.6, 0])
        example = equation(r"(+\;0\;-)_{3}=8", "(+ 0 −)₃ = 8", 48).move_to([0, -1.9, 0])
        self.play(Write(expansion))
        self.pause(4)
        self.play(Write(example), Circumscribe(digits, color=GOLD))
        self.finish()


# ======================= SCENE 03 — STATUS ================================
class Slide03ProposalToImplementation(Chapter):
    chapter_index = 3

    def construct(self):
        self.begin("From proposal to implementation")
        root = label("RUBIDIUM", 42).move_to([0, 1.9, 0])
        tb = circuit_block("TERBIUM 65", 3.5, 1.0).move_to([-3.1, 0, 0])
        co = circuit_block("COBALT", 3.5, 1.0, COBALT).move_to([3.1, 0, 0])
        branches = VGroup(*(wire(root.get_bottom(), b.get_top(), elbow=True) for b in [tb, co]))
        self.reveal(root)
        self.play(Create(branches)); self.reveal(tb, co)
        descriptions = VGroup(label("Ternary logic simulator", 24).next_to(tb, DOWN),
                              label("Ternary computer", 24).next_to(co, DOWN))
        self.reveal(descriptions); self.pause(4)
        working = status("WORKING", POS).move_to([-3.1, -1.55, 0])
        progress = status("IN PROGRESS", COBALT).move_to([3.1, -1.55, 0])
        bottleneck = label("Writable memory bottleneck", 21, MUTED).move_to([3.1, -2.15, 0])
        self.reveal(working, progress, bottleneck); self.pause(6)
        section_transition(self, "Arithmetic opened another direction…")
        self.finish()


# ======================= SCENE 04 — SIMULATOR =============================
class Slide04Terbium65(Chapter):
    chapter_index = 4

    def construct(self):
        self.begin("Terbium 65")
        shot = screenshot_frame(TERBIUM_MAIN_IMAGE, "Terbium 65 — Simulator Screenshot", 8.0, 4.65).move_to([-2, -0.05, 0])
        self.reveal(shot)
        features = ["Unity + C#", "Open source", "~24 components", "ROM support",
                    "Reusable / hierarchical\ncircuits", "Interactive ternary\nsimulation"]
        items = VGroup(*(label(t, 24, POS if i == 0 else INK, width=3.3) for i, t in enumerate(features)))
        items.arrange(DOWN, aligned_edge=LEFT, buff=0.34).move_to([4.4, 0.1, 0])
        for item in items:
            self.reveal(item); self.pause(2)
        self.finish()


# ======================= SCENE 05 — COMPOSITION ===========================
class Slide05BuildingTernaryLogic(Chapter):
    chapter_index = 5

    def construct(self):
        self.begin("Building ternary logic")
        primitives = VGroup(*(circuit_block(t, 1.55) for t in ["MIN", "MAX", "ISN", "ISZ", "ISP"]))
        primitives.arrange(RIGHT, buff=0.5).move_to([0, 1.65, 0])
        self.reveal(*primitives); self.pause(4)
        mux = circuit_block("3:1 MUX", 2.1).move_to([-2.7, -0.55, 0])
        demux = circuit_block("1:3 DEMUX", 2.3).move_to([2.7, -0.55, 0])
        connections = VGroup(*(wire(p.get_bottom(), m.get_top()) for p in primitives for m in [mux, demux]))
        self.play(Create(connections)); self.reveal(mux, demux)
        self.play(Indicate(primitives[0], color=GOLD), Indicate(primitives[1], color=GOLD))
        for line in [connections[4], connections[5]]:
            dot = Dot(line.get_start(), color=GOLD)
            self.add(dot); self.play(MoveAlongPath(dot, line)); self.remove(dot)
        note = label("Complex components compose simpler logic", 28, GOLD).move_to([0, -2.2, 0])
        self.reveal(note); self.pause(5)
        self.clear_body()
        shots = Group(screenshot_frame(ASSETS["mux3"], "3:1 MUX — MIN / MAX + state detectors", 6.0, 3.8),
                      screenshot_frame(ASSETS["demux3"], "1:3 DEMUX — selected signal path", 6.0, 3.8))
        shots.arrange(RIGHT, buff=0.35).move_to([0, 0, 0])
        self.reveal(*shots)
        self.finish()


# ======================= SCENE 06 — HIERARCHY =============================
class Slide06PowersOfThree(Chapter):
    chapter_index = 6

    def construct(self):
        self.begin("Scaling in powers of three")
        tree = routing_tree(1).scale(0.82).move_to([0, -0.05, 0])
        power = equation(r"3^1=3", "3¹ = 3", 40).move_to([0, 2.2, 0])
        self.play(Write(power), Create(tree)); self.pause(4)
        for depth, plain in [(2, "3² = 9"), (3, "3³ = 27")]:
            next_tree = routing_tree(depth).scale(0.82).move_to([0, -0.05, 0])
            next_power = equation(f"3^{depth}={3**depth}", plain, 40).move_to(power)
            self.play(ReplacementTransform(tree, next_tree), ReplacementTransform(power, next_power), run_time=1.5)
            tree, power = next_tree, next_power
            self.pause(4)
        directions = label("MUX   3:1 → 9:1 → 27:1     |     DEMUX   1:3 → 1:9 → 1:27", 25, POS, width=12).move_to([0, -2.6, 0])
        self.reveal(directions); self.pause(3)
        reverse = routing_tree(3, reverse=True).scale(0.82).move_to(tree)
        self.play(ReplacementTransform(tree, reverse)); self.pause(3)
        self.clear_body()
        grid = Group(*(screenshot_frame(ASSETS[key], caption, 3.8, 1.65)
                       for key, caption in [("mux3", "3:1 MUX"), ("mux9", "9:1 MUX"), ("mux27", "27:1 MUX"),
                                            ("demux3", "1:3 DEMUX"), ("demux9", "1:9 DEMUX"), ("demux27", "1:27 DEMUX")]))
        grid.arrange_in_grid(rows=2, cols=3, buff=(0.4, 0.4)).move_to([0, 0.3, 0])
        self.reveal(*grid); self.pause(4)
        self.clear_body()
        rule = equation(r"N=3^k", "N = 3ᵏ", 64).move_to([0, 0.6, 0])
        meaning = label("k selector trits → 3ᵏ possible selections", 30, POS).move_to([0, -0.7, 0])
        self.play(Write(rule)); self.reveal(meaning)
        self.finish()


# ======================= SCENE 07 — MEMORY ================================
class Slide07CobaltMemory(Chapter):
    chapter_index = 7

    def construct(self):
        self.begin("Cobalt and the memory problem")
        intent = label("The intended ternary computer architecture", 24, COBALT).move_to([0, 2.25, 0])
        progress = VGroup(*(status(text, POS) for text in ["Logic  ✓", "Routing  ✓", "Arithmetic  ✓", "ROM  ✓"]))
        progress.arrange(RIGHT, buff=0.6).move_to([0, 1.2, 0])
        question = status("Writable memory  ?", GOLD).move_to([0, 0.25, 0])
        self.reveal(intent, progress, question); self.pause(6)
        self.clear_body()
        logic = circuit_block("COMPUTE", 2.6, 1.15).move_to([-2.4, 0.6, 0])
        memory = circuit_block("RETAIN Q  ?", 2.6, 1.15, GOLD).move_to([2.5, 0.6, 0])
        captions = VGroup(label("Calculate a state", 24).next_to(logic, DOWN, buff=0.4),
                          label("Keep it after the input changes", 23, width=5.0).next_to(memory, DOWN, buff=0.4))
        q = equation(r"Q\in\{-1,0,+1\}", "Q ∈ {−1, 0, +1}", 36).move_to([0, 2.15, 0])
        driving = trit(-1).move_to([-5.15, 0.6, 0])
        self.reveal(q, logic, memory, captions, driving)
        link = wire(driving, logic); self.play(Create(link))
        stored = trit(-1).move_to([5.15, 0.6, 0]); self.reveal(stored)
        for value in [0, 1]:
            new = trit(value).move_to(driving)
            self.play(ReplacementTransform(driving, new)); driving = new
            self.play(Indicate(logic)); self.pause(2)
        uncertain = label("Required: retain the written −1", 22, GOLD).move_to([2.5, -1.5, 0])
        self.reveal(uncertain)
        self.pause(4)
        # Show all writable states as requirements, not a demonstrated memory device.
        all_states = label("Required: write and retain any of the three states", 22, GOLD, width=6.3).move_to(uncertain)
        self.play(ReplacementTransform(uncertain, all_states))
        uncertain = all_states
        for value in [0, 1]:
            new = trit(value).move_to(stored)
            self.play(ReplacementTransform(stored, new)); stored = new
            self.pause(1)
        self.play(FadeOut(uncertain))
        note = label("Current bottleneck: practical ternary writable memory", 27, GOLD, width=12).move_to([0, -2.45, 0])
        self.reveal(note)
        self.finish()


# ======================= SCENE 08 — NEURON MATH ===========================
class Slide08LogicToNeuron(Chapter):
    chapter_index = 8

    def construct(self):
        self.begin("From logic to a neuron")
        inputs = VGroup(*(equation(f"x_{i}", f"x{i}", 36) for i in range(1, 4))).arrange(RIGHT, buff=2.2).move_to([0, 1.8, 0])
        self.reveal(*inputs); self.pause(3)
        products = VGroup(*(equation(f"p_{i}=x_{i}w_{i}", f"p{i} = x{i}w{i}", 33)
                            for i in range(1, 4))).arrange(RIGHT, buff=0.85).move_to([0, 0.7, 0])
        for x, p in zip(inputs, products):
            self.play(TransformFromCopy(x, p)); self.pause(1)
        steps = [
            (r"s=p_1+p_2+p_3", "s = p₁ + p₂ + p₃"),
            (r"z=s+b", "z = s + b"),
            (r"y=f(z)", "y = f(z)")]
        current = equation(*steps[0], size=42).move_to([0, -0.8, 0])
        self.play(Write(current)); self.pause(4)
        for tex, plain in steps[1:]:
            nxt = equation(tex, plain, 42).move_to(current)
            self.play(ReplacementTransform(current, nxt)); current = nxt
            self.pause(3)
        self.clear_body()
        formula = equation(r"y=f\!\left(\sum_{i=1}^{3}x_iw_i+b\right)", "y = f( ∑ᵢ₌₁³ xᵢwᵢ + b )", 48).move_to([0, 1.5, 0])
        activation = equation(r"f(z)=\max(0,z)", "f(z) = max(0, z)", 39).move_to([3.1, -0.05, 0])
        axes = Axes(x_range=[-2, 2, 1], y_range=[0, 2, 1], x_length=4.2, y_length=1.7,
                    tips=False, axis_config={"color": MUTED, "include_ticks": False}).move_to([-3.2, -0.4, 0])
        graph = axes.plot(lambda z: max(0, z), x_range=[-2, 2], color=GOLD)
        self.play(Write(formula)); self.pause(3)
        self.reveal(axes, activation); self.play(Create(graph))
        quantized = label("ReLU-like in a finite, quantized ternary circuit", 23, MUTED).move_to([0, -1.95, 0])
        pipeline = label("MULTIPLY → ACCUMULATE → BIAS → ACTIVATE", 27, POS).move_to([0, -2.7, 0])
        self.reveal(quantized, pipeline)
        self.finish()


# ======================= SCENE 09 — WIDTHS / CIRCUIT ======================
class Slide09BuildingTernaryNeuron(Chapter):
    chapter_index = 9

    def construct(self):
        self.begin("Building the ternary neuron")
        definitions = label("Tₓ: input width     T_w: weight width", 25, MUTED).move_to([0, 2.05, 0])
        product = equation(r"T_p\approx T_x+T_w", "Tₚ ≈ Tₓ + T_w", 43).move_to([0, 0.95, 0])
        acc = equation(r"T_{\mathrm{acc}}\approx T_p+\lceil\log_3N\rceil", "Tacc ≈ Tₚ + ⌈log₃ N⌉", 43).move_to([0, -0.2, 0])
        three = equation(r"N=3:\quad\lceil\log_3 3\rceil=1\quad\Rightarrow\quad T_{\mathrm{acc}}\approx T_p+1",
                         "N = 3:   ⌈log₃ 3⌉ = 1   →   Tacc ≈ Tₚ + 1", 35).move_to([0, -1.4, 0])
        caveat = label("Engineering estimates; check exact ranges and bias headroom", 23, GOLD).move_to([0, -2.5, 0])
        self.reveal(definitions); self.play(Write(product)); self.pause(3)
        self.play(Write(acc)); self.pause(4)
        self.play(Write(three)); self.reveal(caveat); self.pause(5)
        self.clear_body()
        architecture = neuron_architecture().move_to([0, 0.3, 0])
        self.play(Create(architecture[0])); self.reveal(*architecture[1:]); self.pause(4)
        chain = label("EQUATION → ARCHITECTURE → ACTUAL TERBIUM CIRCUIT", 26, GOLD).move_to([0, -2.4, 0])
        self.reveal(chain); self.pause(2)
        self.clear_body()
        screenshot = screenshot_frame(NEURON_IMAGE, "Implemented three-input ternary neuron", 12.3, 4.6).move_to([0, 0.15, 0])
        self.reveal(screenshot)
        self.finish()


# ======================= SCENE 10 — NETWORK ===============================
class Slide10NeuronToNetwork(Chapter):
    chapter_index = 10

    def construct(self):
        self.begin("From one neuron to a network")
        single = neuron("h").move_to([0, 0.4, 0]); self.reveal(single); self.pause(2)
        hidden = VGroup(*(neuron(f"h{i}").move_to([0, y, 0]) for i, y in zip(range(1, 4), [1.6, 0.2, -1.2])))
        self.play(ReplacementTransform(single, hidden[1]),
                  TransformFromCopy(single, hidden[0]), TransformFromCopy(single, hidden[2]))
        inputs = VGroup(*(neuron(f"x{i}", color=ZERO).move_to([-4, y, 0])
                          for i, y in zip(range(1, 4), [1.6, 0.2, -1.2])))
        output = neuron("y", color=GOLD).move_to([4, 0.2, 0])
        self.reveal(*inputs, output)
        in_links = network_connections(inputs, hidden)
        out_links = network_connections(hidden, [output], POS)
        self.play(LaggedStart(*(Create(w) for w in in_links), lag_ratio=0.1), run_time=1.7)
        self.play(Create(out_links)); self.pause(3)
        self.play(LaggedStart(*(Indicate(n, color=GOLD) for n in hidden), lag_ratio=0.25))
        topology = label("3 → 3 → 1", 36, POS).move_to([0, 2.3, 0])
        eqs = VGroup(equation(r"\mathbf h=f(W_h\mathbf x+\mathbf b_h)", "h = f(Wₕ x + bₕ)", 33),
                     equation(r"y=f(W_o\mathbf h+b_o)", "y = f(Wₒ h + bₒ)", 33)).arrange(RIGHT, buff=1.2).move_to([0, -2.3, 0])
        self.reveal(topology); self.play(Write(eqs)); self.pause(6)
        self.clear_body()
        self.reveal(screenshot_frame(NETWORK_IMAGE, "Experimental 3 → 3 → 1 feed-forward network", 12.1, 4.7).move_to([0, 0.15, 0]))
        self.finish()


def verification_data():
    """Never turn unknown, malformed or inconsistent measurements into a pass."""
    numeric = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    vectors = all(isinstance(v, (list, tuple)) and len(v) == 3 and all(numeric(x) for x in v)
                  for v in [TEST_INPUTS, TEST_WEIGHTS])
    computed = max(0, sum(x * w for x, w in zip(TEST_INPUTS, TEST_WEIGHTS)) + TEST_BIAS) if vectors and numeric(TEST_BIAS) else None
    outputs_known = numeric(EXPECTED_OUTPUT) and numeric(TERBIUM_OUTPUT)
    equal = outputs_known and EXPECTED_OUTPUT == TERBIUM_OUTPUT
    consistent = computed is None or computed == EXPECTED_OUTPUT
    return computed, outputs_known, bool(equal and consistent)


# ======================= SCENE 11 — VERIFICATION ==========================
class Slide11Verification(Chapter):
    chapter_index = 11

    def construct(self):
        self.begin("Does it actually work?")
        computed, known, passed = verification_data()
        manual = circuit_block("MANUAL CALCULATION", 4.2, color=GOLD).move_to([-3.1, 1.5, 0])
        simulator = circuit_block("TERBIUM SIMULATION", 4.2).move_to([3.1, 1.5, 0])
        self.reveal(manual, simulator)
        expected_text = str(EXPECTED_OUTPUT) if EXPECTED_OUTPUT is not None else "E (not supplied)"
        simulated_text = str(TERBIUM_OUTPUT) if TERBIUM_OUTPUT is not None else "S (not supplied)"
        expected = label(f"Expected: {expected_text}", 28, width=5.4).move_to([-3.1, 0.35, 0])
        simulated = label(f"Simulated: {simulated_text}", 28, width=5.4).move_to([3.1, 0.35, 0])
        self.play(GrowArrow(Arrow(manual.get_bottom(), expected.get_top(), buff=0.15, color=GOLD)))
        self.reveal(expected); self.pause(3)
        self.play(GrowArrow(Arrow(simulator.get_bottom(), simulated.get_top(), buff=0.15, color=POS)))
        self.reveal(simulated); self.pause(3)
        if computed is not None:
            values = label(f"x = {TEST_INPUTS}   w = {TEST_WEIGHTS}   b = {TEST_BIAS}\nManual max(0, Σxᵢwᵢ + b) = {computed}", 21, MUTED, width=12).move_to([0, -0.75, 0])
            self.reveal(values)
        comparison = ("EXPECTED = SIMULATED   ✓" if passed else
                      "Mismatch / inconsistent manual result" if known else "EXPECTED  ?=  SIMULATED")
        compare = label(comparison, 31, POS if passed else GOLD, width=12).move_to([0, -1.5, 0])
        self.reveal(compare)
        self.pause(4)
        self.clear_body()
        claim = label("Arithmetic/inference path verified", 35, POS, width=12).move_to([0, 1.1, 0])
        attribution = label("Project-reported manual / mathematical checks", 21, MUTED).move_to([0, 0.35, 0])
        audit = label("Populate measured values above to reproduce a comparison", 21, GOLD, width=12).move_to([0, -0.3, 0])
        limits = label("Current network remains a proof of concept;\nit has not yet been scaled/trained for\nmeaningful real-world prediction.", 27, INK, width=12).move_to([0, -1.65, 0])
        self.reveal(claim, attribution, audit, limits)
        self.finish()


# ======================= SCENE 12 — THEN / NOW / NEXT =====================
class Slide12Conclusion(Chapter):
    chapter_index = 12

    def construct(self):
        self.begin("Where Rubidium stands")
        columns = VGroup()
        lists = [
            ("THEN", MUTED, ["Ternary computing concept", "Terbium proposed", "Cobalt proposed"]),
            ("NOW", POS, ["Terbium operational", "Unity + C# · open source", "~24 components · ROM", "3 / 9 / 27-way routing", "Multi-trit arithmetic", "Ternary neuron · 3 → 3 → 1", "Mathematical verification", "Cobalt: memory bottleneck"]),
            ("NEXT", GOLD, ["Practical writable memory", "Continue Cobalt", "Scale neural architecture", "Training / weight generation", "Practical inference task"])]
        for x, (heading, color, entries) in zip([-4.5, 0, 4.5], lists):
            head = label(heading, 31, color).move_to([x, 2, 0])
            lines = VGroup(*(label(t, 21, width=3.9) for t in entries)).arrange(DOWN, aligned_edge=LEFT, buff=0.23)
            lines.next_to(head, DOWN, buff=0.45)
            lines.set_x(x)
            columns.add(VGroup(head, lines))
        for col in columns:
            self.reveal(col); self.pause(4)
        self.pause(3); self.clear_body()
        self.play(FadeOut(self.header))
        states = VGroup(*(trit(v, 0.48) for v in [-1, 0, 1])).arrange(RIGHT, buff=1.3).move_to([0, 1.15, 0])
        self.reveal(*states); self.pause(2)
        self.reveal(label("RUBIDIUM", 64).move_to([0, -0.4, 0]))
        self.reveal(label("Computing beyond two states.", 25, MUTED).move_to([0, -1.45, 0]))
        self.finish()


SCENE_NAMES = ["Slide01Title", "Slide02TernaryRecap", "Slide03ProposalToImplementation",
               "Slide04Terbium65", "Slide05BuildingTernaryLogic", "Slide06PowersOfThree",
               "Slide07CobaltMemory", "Slide08LogicToNeuron", "Slide09BuildingTernaryNeuron",
               "Slide10NeuronToNetwork", "Slide11Verification", "Slide12Conclusion"]
