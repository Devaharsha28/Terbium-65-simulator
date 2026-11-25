"""Cobalt: Complete 30-scene Manim CE presentation matching the latest slide deck."""
from pathlib import Path
import os, warnings
from manim import *

ROOT = Path(__file__).resolve().parent

# ── Minimal Dark Palette ──────────────────────────────────────────
BG      = '#080E18'
PANEL   = '#142032'
ACCENT  = '#3D6DF2'   # Cobalt accent
INK     = '#EEF1F5'   # Off-white body text
MUTED   = '#99A4B2'   # Grey metadata & headers
NEG     = '#EF7972'   # Coral for -1
POS     = '#60BDEC'   # Sky blue for +1
GOLD    = '#EBC76A'
PURPLE  = '#A78BFA'

config.background_color = BG
config.frame_width  = 14.2222222222
config.frame_height = 8

FONT = 'Segoe UI'

# ── Typography & Layout Helpers ────────────────────────────────────

def label(s, size=36, color=INK, max_width=12.8, font=FONT):
    t = Text(s, font=font, font_size=size, color=color, line_spacing=1.0)
    if t.width > max_width:
        t.scale_to_fit_width(max_width)
    return t

def title(s, size=46, color=INK):
    return label(s, size, color)

def header(num, section=''):
    """Top bar: RUBIDIUM • TERNARY COMPUTING (left), XX / 30 (right), and // SECTION."""
    grp = VGroup()
    top_left = label('RUBIDIUM  •  TERNARY COMPUTING', 18, MUTED, max_width=6.0).move_to([-4.4, 3.55, 0])
    top_right = label(f'{num:02d} / 30', 18, MUTED, max_width=2.5).move_to([5.8, 3.55, 0])
    grp.add(top_left, top_right)
    if section:
        sec = label(f'// {section}', 20, ACCENT, max_width=5.0).move_to([-4.8, 2.9, 0])
        grp.add(sec)
    return grp

def card(w=5.2, h=2.2, stroke=ACCENT):
    return RoundedRectangle(
        width=w, height=h, corner_radius=0.12,
        stroke_color=stroke, stroke_width=2,
        fill_color=PANEL, fill_opacity=1,
    )

def card_box(heading, body='', w=5.2, h=2.2, stroke=ACCENT):
    c = card(w, h, stroke)
    t = label(heading, 30, INK, w - 0.4)
    if body:
        b = label(body, 20, MUTED, w - 0.4)
        grp = VGroup(t, b).arrange(DOWN, buff=0.16).move_to(c)
        return VGroup(c, grp)
    t.move_to(c)
    return VGroup(c, t)

def safe_image(name, width=12.0, height=6.0):
    path = ROOT / 'assets' / name
    if path.is_file():
        try:
            m = ImageMobject(str(path))
            m.scale(min(width / m.width, height / m.height))
            return m
        except Exception as exc:
            warnings.warn(f'Cannot load {name}: {exc}')
    r = Rectangle(width=width, height=height, color=MUTED,
                  fill_color=PANEL, fill_opacity=1)
    t = label(name, 24, MUTED, width - 0.6).move_to(r.get_center() + UP * 0.2)
    m = label('IMAGE NOT FOUND', 18, MUTED).move_to(r.get_center() + DOWN * 0.4)
    return VGroup(r, t, m)

class Slide(Scene):
    pass


# =====================================================================
# 30 SCENES (MATCHING LATEST DECK)
# =====================================================================

# 1. Chip Cover Slide
class C01_Chip(Slide):
    def construct(self):
        img = safe_image('chip_full.png', 14.22, 8.0)
        img.set_opacity(0)
        self.add(img)

        tag1 = label('RUBIDIUM', 28, INK).move_to([-4.8, 3.2, 0]).set_z_index(3)
        tag2 = label('Ternary Computing System', 20, MUTED).move_to([-4.8, 2.7, 0]).set_z_index(3)
        tags = VGroup(tag1, tag2)
        tags.set_opacity(0)

        self.play(img.animate.set_opacity(1), tags.animate.set_opacity(1), run_time=2.5)
        self.wait(1)

# 2. Team & Project
class C02_OurProject(Slide):
    def construct(self):
        h = header(2, 'TEAM')
        t = title('Rubidium', 50).move_to([0, 2.7, 0])
        crest = safe_image('gioe_logo.png', 2.3, 2.3).move_to([0, 1.25, 0])
        self.play(FadeIn(h), FadeIn(t), FadeIn(crest), run_time=1.0)

        row1 = label('D Deva Harsha   •   V Abhiram Patel   •   G Shiva Prasad', 23)
        row2 = label('M Joy Samanvith Raj   •   D Arjun Gnanadeep', 23)
        names = VGroup(row1, row2).arrange(DOWN, buff=0.22).move_to([0, -0.45, 0])
        self.play(LaggedStart(*(FadeIn(r) for r in (row1, row2)), lag_ratio=0.15), run_time=1.0)

        guide = label('Guide: A. Sateesh Naik, B.E., Lecturer in ECE', 21, MUTED).move_to([0, -1.75, 0])
        inst1 = label('Government Institute of Electronics, Secunderabad', 20, MUTED).move_to([0, -2.4, 0])
        inst2 = label('Diploma in Cyber Physical Systems and Security, 2024-2027', 18, MUTED).move_to([0, -2.95, 0])
        self.play(FadeIn(guide), FadeIn(inst1), FadeIn(inst2), run_time=1.0)
        self.wait(1)

# 3. Binary
class C03_Binary(Slide):
    def construct(self):
        h = header(3, 'BACKGROUND')
        t = title('Binary', 52).move_to([0, 1.8, 0])
        self.play(FadeIn(h), FadeIn(t))
        digits = label('0    1', 110, INK).move_to([0, -0.5, 0])
        self.play(FadeIn(digits), run_time=1.0)
        self.wait(1)

# 4. Ternary
class C04_Ternary(Slide):
    def construct(self):
        h = header(4, 'BACKGROUND')
        t = title('Ternary', 52).move_to([0, 1.8, 0])
        self.play(FadeIn(h), FadeIn(t))
        d_m = label('-1', 110, NEG)
        d_0 = label('0', 110, MUTED)
        d_p = label('+1', 110, POS)
        row = VGroup(d_m, d_0, d_p).arrange(RIGHT, buff=1.8).move_to([0, -0.5, 0])
        self.play(LaggedStart(*(FadeIn(d) for d in (d_m, d_0, d_p)), lag_ratio=0.2), run_time=1.2)
        self.wait(1)

# 5. Quantum
class C05_Quantum(Slide):
    def construct(self):
        h = header(5, 'BACKGROUND')
        t = title('Quantum', 52).move_to([0, 2.2, 0])
        self.play(FadeIn(h), FadeIn(t))
        k0 = label('|0⟩', 60, INK)
        k1 = label('|1⟩', 60, INK)
        kpsi = label('|ψ⟩', 60, ACCENT)
        col = VGroup(k0, k1, kpsi).arrange(DOWN, buff=0.6).move_to([0, -0.4, 0])
        self.play(LaggedStart(*(FadeIn(k) for k in col), lag_ratio=0.2), run_time=1.2)
        self.wait(1)

# 6. Neuromorphic
class C06_Neuromorphic(Slide):
    def construct(self):
        h = header(6, 'BACKGROUND')
        t = title('Neuromorphic', 48).move_to([-3.4, 1.6, 0])
        sub = label('Brain-based computing', 28, MUTED).move_to([-3.4, 0.8, 0])
        self.play(FadeIn(h), FadeIn(t), FadeIn(sub))

        # Neural network visual matching the slide diagram
        in_pos = [LEFT * 0.5 + UP * y for y in (1.6, 0.0, -1.6)]
        hid_pos = [RIGHT * 2.5 + UP * y for y in (2.1, 0.7, -0.7, -2.1)]
        out_pos = [RIGHT * 5.2 + UP * 0.0]

        in_nodes = [Circle(0.28, color=PURPLE, fill_color=PURPLE, fill_opacity=0.9).move_to(p) for p in in_pos]
        hid_nodes = [Circle(0.28, color=PURPLE, fill_color=PURPLE, fill_opacity=0.9).move_to(p) for p in hid_pos]
        out_nodes = [Circle(0.35, color=PURPLE, fill_color=PURPLE, fill_opacity=0.9).move_to(p) for p in out_pos]

        edges = VGroup()
        for i in in_nodes:
            for j in hid_nodes:
                edges.add(Line(i.get_center(), j.get_center(), color=MUTED, stroke_width=1.5))
        for j in hid_nodes:
            for k in out_nodes:
                edges.add(Line(j.get_center(), k.get_center(), color=MUTED, stroke_width=1.5))

        all_nodes = VGroup(*in_nodes, *hid_nodes, *out_nodes)
        self.play(FadeIn(edges), LaggedStart(*(FadeIn(n) for n in all_nodes), lag_ratio=0.06), run_time=1.4)
        self.wait(1)

# 7. Different computing
class C07_Compare(Slide):
    def construct(self):
        h = header(7, 'BACKGROUND')
        t = title('Different computing', 48).move_to([0, 2.5, 0])
        self.play(FadeIn(h), FadeIn(t))

        c1 = card_box('Binary', w=5.2, h=2.0).move_to([-3.2, 0.9, 0])
        c2 = card_box('Ternary', w=5.2, h=2.0).move_to([3.2, 0.9, 0])
        c3 = card_box('Quantum', w=5.2, h=2.0).move_to([-3.2, -1.6, 0])
        c4 = card_box('Neuromorphic', w=5.2, h=2.0).move_to([3.2, -1.6, 0])

        self.play(LaggedStart(*(FadeIn(c) for c in (c1, c2, c3, c4)), lag_ratio=0.15), run_time=1.5)
        self.wait(1)

# 8. Units of ternary
class C08_TernaryUnits(Slide):
    def construct(self):
        h = header(8, 'BACKGROUND')
        t = title('Units of ternary', 48).move_to([0, 2.5, 0])
        self.play(FadeIn(h), FadeIn(t))

        u1 = label('trit', 60, INK).move_to([0, 0.8, 0])
        u2 = label('tryte', 60, INK).move_to([0, -0.6, 0])
        eq = label('9 trits = 1 tryte', 34, MUTED).move_to([0, -2.1, 0])

        self.play(FadeIn(u1), FadeIn(u2), FadeIn(eq), run_time=1.2)
        self.wait(1)

# 9. Current research
class C09_CurrentResearch(Slide):
    def construct(self):
        h = header(9, 'RESEARCH')
        t = title('Current research', 60).move_to([0, 0.0, 0])
        self.play(FadeIn(h), FadeIn(t), run_time=1.2)
        self.wait(1)

# 10. Microsoft BitNet
class C10_BitNet(Slide):
    def construct(self):
        h = header(10, 'RESEARCH')
        t = title('Microsoft BitNet', 46).move_to([0, 2.6, 0])
        im1 = safe_image('bitnet.png', 6.0, 3.8).move_to([-3.4, -0.2, 0])
        im2 = safe_image('network_diagram.png', 6.0, 3.8).move_to([3.4, -0.2, 0])
        self.play(FadeIn(h), FadeIn(t))
        self.play(FadeIn(im1), FadeIn(im2), run_time=1.2)
        self.wait(1)

# 11. Huawei
class C11_Huawei(Slide):
    def construct(self):
        h = header(11, 'RESEARCH')
        t = title('Huawei', 48).move_to([0, 2.7, 0])
        img = safe_image('huawei.png', 6.0, 3.6).move_to([-3.4, -0.4, 0])

        p1 = label('Ternary logic gate patent', 28, INK).move_to([3.4, 0.4, 0])
        p2 = label('CN119652311A', 26, ACCENT).move_to([3.4, -0.3, 0])
        p3 = label('Filed September 2023', 24, MUTED).move_to([3.4, -1.0, 0])
        txt = VGroup(p1, p2, p3)

        self.play(FadeIn(h), FadeIn(t), FadeIn(img), FadeIn(txt), run_time=1.2)
        self.wait(1)

# 12. Tern Computing
class C12_TernaryStartup(Slide):
    def construct(self):
        h = header(12, 'RESEARCH')
        t = title('Tern Computing', 50).move_to([0, 2.5, 0])
        img = safe_image('startup.png', 4.4, 4.4).move_to([0, -0.4, 0])
        self.play(FadeIn(h), FadeIn(t), FadeIn(img), run_time=1.2)
        self.wait(1)

# 13. GDDR7
class C13_GDDR7(Slide):
    def construct(self):
        h = header(13, 'RESEARCH')
        t = title('GDDR7', 48).move_to([0, 2.7, 0])
        im_gpu = safe_image('nvidia_5090.png', 5.6, 3.2).move_to([-3.4, 0.6, 0])
        im_mem = safe_image('memory_makers.png', 5.6, 3.2).move_to([3.4, 0.6, 0])

        lbl_gpu = label('RTX 5090 GPU', 26, INK).move_to([0, -1.7, 0])
        lbl_pam = label('GDDR7 uses PAM3 signalling: 3 voltage levels', 26, MUTED).move_to([0, -2.5, 0])

        self.play(FadeIn(h), FadeIn(t))
        self.play(FadeIn(im_gpu), FadeIn(im_mem), FadeIn(lbl_gpu), FadeIn(lbl_pam), run_time=1.2)
        self.wait(1)

# 14. Our project split
class C14_ProjectSplit(Slide):
    def construct(self):
        h = header(14, 'PROJECT')
        t = title('Our project', 50).move_to([0, 2.5, 0])
        self.play(FadeIn(h), FadeIn(t))

        c1 = card_box('Terbium', w=5.2, h=3.0).move_to([-3.4, -0.4, 0])
        c2 = card_box('Cobalt', w=5.2, h=3.0).move_to([3.4, -0.4, 0])
        self.play(FadeIn(c1), FadeIn(c2), run_time=1.2)
        self.wait(1)

# 15. Terbium
class C15_Terbium(Slide):
    def construct(self):
        h = header(15, 'TERBIUM')
        t = title('Terbium', 56).move_to([0, 1.2, 0])
        sub = label('Ternary circuit simulator', 34, MUTED).move_to([0, -0.6, 0])
        self.play(FadeIn(h), FadeIn(t), FadeIn(sub), run_time=1.0)
        self.wait(1)

# 16. Terbium tools
class C16_TerbiumTools(Slide):
    def construct(self):
        h = header(16, 'TERBIUM')
        t = title('Terbium tools', 50).move_to([0, 2.7, 0])

        u_img = safe_image('unity_logo.png', 2.2, 2.2).move_to([-3.4, 0.5, 0])
        u_txt = label('Unity', 34, INK).move_to([-3.4, -1.2, 0])

        c_img = safe_image('csharp_logo.png', 2.2, 2.2).move_to([3.4, 0.5, 0])
        c_txt = label('C#', 34, INK).move_to([3.4, -1.2, 0])

        self.play(FadeIn(h), FadeIn(t))
        self.play(FadeIn(u_img), FadeIn(u_txt), FadeIn(c_img), FadeIn(c_txt), run_time=1.2)
        self.wait(1)

# 17. Terbium interface
class C17_TerbiumInterface(Slide):
    def construct(self):
        h = header(17, 'TERBIUM')
        t = title('Terbium interface', 40).move_to([0, 2.8, 0])
        img = safe_image('terbium_ui.png', 12.8, 5.8).move_to([0, -0.5, 0])
        self.play(FadeIn(h), FadeIn(t), FadeIn(img), run_time=1.0)
        self.wait(1)

# 18. Cobalt R309B1
class C18_Cobalt(Slide):
    def construct(self):
        h = header(18, 'COBALT')
        t = title('Cobalt R309B1', 56).move_to([0, 1.2, 0])
        sub = label('Ternary CPU', 34, MUTED).move_to([0, -0.6, 0])
        self.play(FadeIn(h), FadeIn(t), FadeIn(sub), run_time=1.0)
        self.wait(1)

# 19. Cobalt R309B1: the name
class C19_CobaltName(Slide):
    def construct(self):
        h = header(19, 'COBALT')
        t = title('Cobalt R309B1: the name', 44).move_to([0, 2.7, 0])
        self.play(FadeIn(h), FadeIn(t))

        items = [
            ('COBALT', '27', 'Heptavintimal: base 27, the ternary counterpart of hex', -4.2, 0.7),
            ('R3', 'Radix 3', 'Base-3 number system', 4.2, 0.7),
            ('09', '9 trits', 'One tryte, the native word', -4.2, -1.2),
            ('B1', 'Batch 1', 'First batch of the design', 4.2, -1.2),
        ]
        cards = VGroup()
        for tag, main_t, desc_t, x, y in items:
            box = card(w=5.2, h=1.6)
            b_tag = label(tag, 22, ACCENT).move_to([x - 1.8, y + 0.35, 0])
            b_main = label(main_t, 26, INK).move_to([x + 0.3, y + 0.35, 0])
            b_desc = label(desc_t, 18, MUTED, max_width=4.8).move_to([x, y - 0.35, 0])
            box.move_to([x, y, 0])
            cards.add(VGroup(box, b_tag, b_main, b_desc))

        self.play(LaggedStart(*(FadeIn(c) for c in cards), lag_ratio=0.12), run_time=1.6)

        foot = label('Hex is to binary what heptavintimal is to ternary', 22, MUTED).move_to([0, -2.8, 0])
        self.play(FadeIn(foot))
        self.wait(1)

# 20. Cobalt in Terbium: specifications
class C20_CobaltSpecs(Slide):
    def construct(self):
        h = header(20, 'COBALT')
        t = title('Cobalt in Terbium: specifications', 44).move_to([0, 2.5, 0])
        self.play(FadeIn(h), FadeIn(t))

        specs = [
            'Harvard architecture',
            '9 trits',
            'ROM: 19683 x 9',
            '27 registers',
            'RAM: 27 locations'
        ]
        items = VGroup(*(label(s, 32, INK) for s in specs)).arrange(DOWN, buff=0.45).move_to([0, -0.6, 0])
        self.play(LaggedStart(*(FadeIn(it) for it in items), lag_ratio=0.15), run_time=1.5)
        self.wait(1)

# 21. Cobalt in Terbium
class C21_CobaltInTerbium(Slide):
    def construct(self):
        h = header(21, 'COBALT')
        t = title('Cobalt in Terbium', 40).move_to([0, 2.8, 0])
        img = safe_image('cobalt_in_terbium.png', 12.8, 5.8).move_to([0, -0.5, 0])
        self.play(FadeIn(h), FadeIn(t), FadeIn(img), run_time=1.0)
        self.wait(1)

# 22. Cobalt physical
class C22_CobaltPhysical(Slide):
    def construct(self):
        h = header(22, 'COBALT')
        t = title('Cobalt physical', 40).move_to([0, 2.8, 0])
        img = safe_image('cobalt_chip.png', 6.0, 5.0).move_to([0, 0.0, 0])
        cap = label('Cobalt layout', 26, MUTED).move_to([0, -3.2, 0])
        self.play(FadeIn(h), FadeIn(t), FadeIn(img), FadeIn(cap), run_time=1.0)
        self.wait(1)

# 23. Cobalt: stripped down (ISA)
class C23_CobaltISA(Slide):
    def construct(self):
        h = header(23, 'COBALT')
        t = title('Cobalt: stripped down (ISA)', 40).move_to([0, 2.7, 0])
        self.play(FadeIn(h), FadeIn(t))

        hdr = label('Opcode      Name        Action', 24, ACCENT).move_to([0, 1.9, 0])
        self.play(FadeIn(hdr))

        rows_data = [
            '0            HLT         Stop',
            '1            ADD         r13 = r13 + r14',
            '2            SUB         r13 = r13 - r14',
            '3            MIN         Trit-wise min',
            '4            MAX         Trit-wise max',
            '5            MUL         Trit-wise product',
            '6            MOV         r13 = r14',
            '7            LDA         Load r13 (immediate)',
            '8            LDB         Load r14 (immediate)'
        ]
        rows = VGroup(*(label(r, 22, INK) for r in rows_data)).arrange(DOWN, buff=0.14).move_to([0, -0.35, 0])
        self.play(LaggedStart(*(FadeIn(r) for r in rows), lag_ratio=0.08), run_time=1.8)

        fmt = label('Format: [ opcode (8 bits) | immediate (10 bits) ]', 22, MUTED).move_to([0, -3.2, 0])
        self.play(FadeIn(fmt))
        self.wait(1)

# 24. Tools used
class C24_ToolsUsed(Slide):
    def construct(self):
        h = header(24, 'LAYOUT FLOW')
        t = title('Tools used', 48).move_to([0, 2.5, 0])
        self.play(FadeIn(h), FadeIn(t))

        tools = ['Yosys', 'OpenROAD', 'SkyWater 130nm PDK']
        items = VGroup(*(label(s, 38, INK) for s in tools)).arrange(DOWN, buff=0.6).move_to([0, -0.5, 0])
        self.play(LaggedStart(*(FadeIn(it) for it in items), lag_ratio=0.2), run_time=1.4)
        self.wait(1)

# 25. Cobalt layout: specs
class C25_TechSpecs(Slide):
    def construct(self):
        h = header(25, 'COBALT LAYOUT')
        t = title('Cobalt layout: specifications', 44).move_to([0, 2.6, 0])
        self.play(FadeIn(h), FadeIn(t))

        specs = [
            '40 kHz',
            '7,840 transistors',
            '1.8 V',
            '18-bit instruction',
            '2 registers',
            '16-instruction memory',
            '2 cycles / instruction'
        ]
        items = VGroup(*(label(s, 26, INK) for s in specs)).arrange(DOWN, buff=0.24).move_to([0, 0.15, 0])
        self.play(LaggedStart(*(FadeIn(it) for it in items), lag_ratio=0.1), run_time=1.6)

        fn = label('*estimated: frequency and transistor count; 1.8 V from the SkyWater 130nm PDK', 18, MUTED).move_to([0, -3.1, 0])
        self.play(FadeIn(fn))
        self.wait(1)

# 26. Limitations
class C26_Limitations(Slide):
    def construct(self):
        h = header(26, 'LIMITS')
        t = title('Limitations', 50).move_to([0, 2.5, 0])
        self.play(FadeIn(h), FadeIn(t))

        points = [
            'No physical chip',
            'No wide software',
            'Heat issues',
            'Noise'
        ]
        items = VGroup(*(label(s, 36, INK) for s in points)).arrange(DOWN, buff=0.5).move_to([0, -0.5, 0])
        self.play(LaggedStart(*(FadeIn(it) for it in items), lag_ratio=0.15), run_time=1.5)
        self.wait(1)

# 27. Credits 1
class C27_Credits1(Slide):
    def construct(self):
        h = header(27, 'CREDITS')
        t = title('Credits', 50).move_to([0, 2.6, 0])
        self.play(FadeIn(h), FadeIn(t))

        p1_n = label('Sebastian Lague', 34, INK)
        p1_u = label('Digital Logic Sim: github.com/SebLague/Digital-Logic-Sim', 22, MUTED)
        grp1 = VGroup(p1_n, p1_u).arrange(DOWN, buff=0.2).move_to([0, 0.8, 0])

        p2_n = label('louis-dr', 34, INK)
        p2_u = label('Ternary Computing: louis-dr.github.io/index-ternary.html', 22, MUTED)
        grp2 = VGroup(p2_n, p2_u).arrange(DOWN, buff=0.2).move_to([0, -1.6, 0])

        self.play(FadeIn(grp1), FadeIn(grp2), run_time=1.2)
        self.wait(1)

# 28. Credits 2
class C28_Credits2(Slide):
    def construct(self):
        h = header(28, 'CREDITS')
        t = title('Credits', 50).move_to([0, 2.6, 0])
        self.play(FadeIn(h), FadeIn(t))

        p1_n = label('Douglas W. Jones', 34, INK)
        p1_u = label('Ternary Logic and Arithmetic: homepage.cs.uiowa.edu/~dwjones/ternary/', 22, MUTED)
        grp1 = VGroup(p1_n, p1_u).arrange(DOWN, buff=0.2).move_to([0, 0.8, 0])

        p2_n = label('Setun', 34, INK)
        p2_u = label('Ternary computer, Moscow State University', 24, MUTED)
        grp2 = VGroup(p2_n, p2_u).arrange(DOWN, buff=0.2).move_to([0, -1.6, 0])

        self.play(FadeIn(grp1), FadeIn(grp2), run_time=1.2)
        self.wait(1)

# 29. Questions
class C29_Questions(Slide):
    def construct(self):
        t = title('Questions?', 72).move_to([0, 0, 0])
        self.play(FadeIn(t), run_time=1.5)
        self.wait(1)

# 30. Thank You
class C30_ThankYou(Slide):
    def construct(self):
        t = title('Thank you', 72).move_to([0, 0, 0])
        self.play(FadeIn(t), run_time=1.5)
        self.wait(1)


SCENE_LIST = [
    'C01_Chip', 'C02_OurProject', 'C03_Binary', 'C04_Ternary', 'C05_Quantum', 'C06_Neuromorphic',
    'C07_Compare', 'C08_TernaryUnits', 'C09_CurrentResearch', 'C10_BitNet', 'C11_Huawei', 'C12_TernaryStartup',
    'C13_GDDR7', 'C14_ProjectSplit', 'C15_Terbium', 'C16_TerbiumTools', 'C17_TerbiumInterface', 'C18_Cobalt',
    'C19_CobaltName', 'C20_CobaltSpecs', 'C21_CobaltInTerbium', 'C22_CobaltPhysical', 'C23_CobaltISA',
    'C24_ToolsUsed', 'C25_TechSpecs', 'C26_Limitations', 'C27_Credits1', 'C28_Credits2', 'C29_Questions', 'C30_ThankYou'
]
