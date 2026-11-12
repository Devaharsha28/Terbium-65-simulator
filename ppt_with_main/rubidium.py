"""Rubidium: fifteen independent animated engineering canvases, Manim CE."""
from pathlib import Path
import os, json, warnings
from manim import *
ROOT=Path(__file__).resolve().parent
BG,INK,MUTED='#080E18','#EEF1F5','#99A4B2'
NEG,ZERO,POS,GOLD='#EF7972','#99A4B2','#60BDEC','#EBC76A'
PANEL,COBALT='#142032','#A79BD5'
PACE=float(os.getenv('RUBIDIUM_PACE','1'))
HOLD=1.6
config.background_color=BG
config.frame_width=14.2222222222
config.frame_height=8
ASSETS={'ui':'terbium ui.png','mux27':'27mux.png','demux27':'27demux.png',
 'neuron':'neuron.png','network':'network.png','qr':'terbium-tRsAWc.png','unity':'download.png',
 'mux3':'mux3.png','mux9':'mux9.png','demux3':'demux3.png','demux9':'demux9.png'}

def text(s,size=32,color=INK,width=12.8,font='Segoe UI'):
    m=Text(s,font=font,font_size=size,color=color,line_spacing=0.9)
    if m.width>width: m.scale_to_fit_width(width)
    return m
def mathtext(s,size=40,color=INK,width=12.8):
    return text(s,size,color,width,'Cambria')
def block(s,w=1.8,h=0.9,color=POS):
    box=RoundedRectangle(width=w,height=h,corner_radius=0.08,stroke_color=color,
        stroke_width=2,fill_color=PANEL,fill_opacity=1)
    t=text(s,26,color,w-0.2).move_to(box)
    if t.height>h-0.18: t.scale_to_fit_height(h-0.18)
    return VGroup(box,t)
def link(a,b,color=MUTED):
    return Line(a.get_right(),b.get_left(),stroke_width=2,color=color).set_z_index(-1)
def states(size=52,spacing=1.5):
    return VGroup(text('−1',size,NEG),text('0',size,ZERO),text('+1',size,POS)).arrange(RIGHT,buff=spacing)
def image(key,width=13.5,height=6.8):
    name=ASSETS.get(key,key); path=ROOT/'assets'/name
    if path.is_file():
        try:
            m=ImageMobject(str(path)); m.scale(min(width/m.width,height/m.height))
            m.set_resampling_algorithm(RESAMPLING_ALGORITHMS['nearest'])
            return m
        except (OSError,ValueError) as exc: warnings.warn(f'Image unavailable: {name}: {exc}')
    return VGroup(Rectangle(width=width,height=height,color=MUTED,fill_color=PANEL,fill_opacity=1),
        text(name,28,MUTED,width-0.6),text('IMAGE UNAVAILABLE',18,MUTED).move_to([0,-0.6,0]))
def network():
    ins=VGroup(*(Circle(0.27,color=ZERO,fill_color=BG,fill_opacity=1).move_to([-4.8,y,0]) for y in (1.6,0,-1.6)))
    hidden=VGroup(*(Circle(0.43,color=POS,fill_color=PANEL,fill_opacity=1).move_to([0,y,0]) for y in (1.6,0,-1.6)))
    out=VGroup(Circle(0.5,color=POS,fill_color=PANEL,fill_opacity=1).move_to([4.8,0,0]))
    wires=VGroup(*(link(a,b) for a in ins for b in hidden),*(link(a,out[0]) for a in hidden))
    return VGroup(wires,ins,hidden,out)
def architecture():
    inp=VGroup(*(mathtext(f'x{n}',32).move_to([-6,y,0]) for n,y in zip(('₁','₂','₃'),(1.35,0,-1.35))))
    mul=VGroup(*(block('MUL',1.3).move_to([-4.1,y,0]) for y in (1.35,0,-1.35)))
    weights=VGroup(*(mathtext(f'w{n}',27,GOLD).next_to(m,UP,buff=0.13) for n,m in zip(('₁','₂','₃'),mul)))
    add=block('ADD',1.45,1.6).move_to([-1.4,0,0]); bias=block('BIAS',1.4,color=GOLD).move_to([1,0,0])
    act=block('ACTIVATION /\nTERNARY\nQUANTIZATION',2.2,1.45,GOLD).move_to([3.7,0,0])
    out=mathtext('y',40,POS).move_to([6,0,0])
    wires=VGroup(*(link(a,b) for a,b in zip(inp,mul)),*(link(a,add) for a in mul),link(add,bias),link(bias,act),link(act,out))
    return VGroup(wires,inp,mul,weights,add,bias,act,out)
def project_tree():
    root=text('RUBIDIUM',58).move_to([0,2.35,0]); t=text('TERBIUM',44,POS).move_to([-3.6,-0.4,0]); c=text('COBALT',44,COBALT).move_to([3.6,-0.4,0])
    lines=VGroup(Line([0,1.8,0],[0,1,0],color=MUTED),Line([-3.6,1,0],[3.6,1,0],color=MUTED),
        Line([-3.6,1,0],[-3.6,0.2,0],color=POS),Line([3.6,1,0],[3.6,0.2,0],color=COBALT))
    return VGroup(root,lines,t,c)

class Canvas(Scene):
    def setup(self):
        super().setup(); self.beats=[]
    def play(self,*animations,**kwargs):
        if not(len(animations)==1 and isinstance(animations[0],Wait)):
            kwargs['run_time']=kwargs.get('run_time',0.85)*PACE
        return super().play(*animations,**kwargs)
    def pause(self,seconds=HOLD):
        self.wait(seconds*PACE)
        bounds=[[round(float(v),3) for v in (m.get_left()[0],m.get_right()[0],m.get_bottom()[1],m.get_top()[1])]
            for m in self.mobjects if m.width and m.height]
        self.beats.append({'time':round(self.time,3),'bounds':bounds})
        if os.getenv('RUBIDIUM_CAPTURE'):
            folder=ROOT/'review15'; folder.mkdir(exist_ok=True); self.renderer.update_frame(self)
            self.camera.get_image().save(folder/f'{type(self).__name__}_{len(self.beats):02}.png')
    def reveal(self,*m):
        self.play(LaggedStart(*(FadeIn(x,shift=UP*0.12) for x in m),lag_ratio=0.12))
    def erase(self):
        if self.mobjects: self.play(*(FadeOut(m) for m in list(self.mobjects)))
    def finish(self,seconds=HOLD):
        self.pause(seconds)
        if os.getenv('RUBIDIUM_CAPTURE'):
            (ROOT/'review15'/f'{type(self).__name__}.json').write_text(json.dumps(
                {'scene':type(self).__name__,'duration':self.time,'beats':self.beats},indent=2))
    def spotlight(self,picture,region,caption,at=UP*3.35):
        x0,y0,x1,y1=region
        ring=RoundedRectangle(width=(x1-x0)*picture.width,height=(y1-y0)*picture.height,corner_radius=0.07,
            color=GOLD,stroke_width=3).move_to(picture.get_center()+np.array([
            ((x0+x1)/2-0.5)*picture.width,(0.5-(y0+y1)/2)*picture.height,0]))
        note=text(caption,28,GOLD).move_to(at)
        self.play(Create(ring),FadeIn(note)); self.pause(1.7); self.play(FadeOut(ring),FadeOut(note))

class Slide01Rubidium(Canvas):
    def construct(self):
        self.wait(0.5); s=states().move_to([0,-0.7,0])
        self.play(LaggedStart(*(FadeIn(m,shift=DOWN*0.5) for m in s),lag_ratio=0.2),run_time=1.25)
        self.play(FadeIn(text('RUBIDIUM',82).move_to([0,0.65,0])),run_time=1.1); self.finish(2)

class Slide02Trit(Canvas):
    def construct(self):
        binary=VGroup(text('0',62,ZERO),text('1',62,POS)).arrange(RIGHT,buff=3); bit=text('BIT',42).move_to([0,-1.5,0])
        self.reveal(binary); self.play(Write(bit)); self.pause(0.7)
        tern=states(62,2); trit=text('TRIT',42).move_to(bit)
        self.play(ReplacementTransform(binary,tern),ReplacementTransform(bit,trit),run_time=1.3)
        counts=VGroup(text('Binary → 2 states',26,MUTED),text('Ternary → 3 states',26,POS)).arrange(RIGHT,buff=1).move_to([0,-2.6,0])
        self.reveal(counts); self.pause(1); self.erase()
        contrast=text('TERNARY ≠ QUANTUM',46).move_to([0,2.8,0]); left=text('TERNARY',32,POS).move_to([-3.6,1.6,0]); right=text('QUANTUM',32,GOLD).move_to([3.5,1.6,0])
        discrete=states(34,1.0).move_to([-3.6,0.3,0])
        circles=VGroup(*(Circle(0.5,color=c).move_to(m) for m,c in zip(discrete,(NEG,ZERO,POS))))
        basis=VGroup(mathtext('|0⟩',36),mathtext('|1⟩',36)).arrange(RIGHT,buff=2.5).move_to([3.5,0.5,0])
        # Normalized amplitude vector, not a continuous classical bit value.
        axes=VGroup(Line([2.35,-1.4,0],[4.4,-1.4,0],color=MUTED),Line([2.35,-1.4,0],[2.35,0.1,0],color=MUTED))
        arc=Arc(radius=1.35,start_angle=0,angle=PI/2,color=GOLD).move_arc_center_to([2.35,-1.4,0])
        amp=Arrow([2.35,-1.4,0],[3.5,-0.7,0],buff=0,color=GOLD)
        al=text('α',24,GOLD).move_to([3.5,-1.7,0]); be=text('β',24,GOLD).move_to([2,-0.7,0])
        self.reveal(contrast,left,right,discrete,circles,basis)
        self.play(Create(axes),Create(arc),GrowArrow(amp),FadeIn(al),FadeIn(be))
        self.play(Rotate(amp,angle=0.35,about_point=[2.35,-1.4,0]),run_time=1.3)
        psi=mathtext('|ψ⟩ = α|0⟩ + β|1⟩',32,GOLD).move_to([3.5,-2.15,0])
        classic=text('Three discrete classical states',23,MUTED,6).move_to([-3.6,-2.15,0])
        self.reveal(psi,classic,text('Superposition of basis states',23,MUTED,6).move_to([3.5,-2.9,0])); self.pause(1.3); self.erase()
        self.reveal(states(58).move_to([0,0.6,0]),text('TERNARY IS CLASSICAL COMPUTING',38).move_to([0,-1,0])); self.finish()

class Slide03InsideRubidium(Canvas):
    def construct(self):
        tree=project_tree(); root=text('RUBIDIUM',76); self.reveal(root); self.play(ReplacementTransform(root,tree[0]))
        self.play(Create(tree[1]),FadeIn(tree[2]),FadeIn(tree[3]),run_time=1.5)
        gate=block('−1   0   +1',2.6,0.8).move_to([-3.6,-2.45,0])
        pins=VGroup(*(Line([2.35+i*0.5,-2.9,0],[2.35+i*0.5,-3.15,0],color=COBALT) for i in range(6)))
        chip=VGroup(block('CPU',2.8,1,COBALT).move_to([3.6,-2.4,0]),pins)
        self.reveal(text('Ternary Logic\nSimulator',27).move_to([-3.6,-1.45,0]),
            text('Ternary Computer\nArchitecture',27).move_to([3.6,-1.45,0]),gate,chip); self.finish()

class Slide04Progress(Canvas):
    def construct(self):
        t=text('TERBIUM v1',48,POS).move_to([-3.5,1.9,0]); c=text('COBALT',48,COBALT).move_to([3.5,1.9,0]); self.reveal(t,c)
        complete=text('COMPLETED ✓',40,POS).move_to([-3.5,0.65,0]); self.play(TransformFromCopy(t,complete))
        concept=VGroup(text('CONCEPTUAL',30,COBALT),text('NOT YET IMPLEMENTED',22,MUTED)).arrange(DOWN,buff=0.2).move_to([3.5,0.6,0])
        self.reveal(concept); self.pause(1)
        pipeline=VGroup(*(VGroup(text(name,26),text(sign,34,col)).arrange(DOWN,buff=0.3)
            for name,sign,col in [('Logic','✓',POS),('Routing','✓',POS),('ROM','✓',POS),('Writable\nMemory','?',GOLD)]))
        pipeline.arrange(RIGHT,buff=0.9).move_to([0,-1.7,0]); self.play(LaggedStart(*(FadeIn(p) for p in pipeline),lag_ratio=0.35),run_time=2); self.pause(1)
        self.play(TransformFromCopy(pipeline[-1][0],text('TERNARY MEMORY',46,GOLD).move_to([0,-3.1,0]))); self.finish()

class Slide05HowTerbiumWasMade(Canvas):
    def construct(self):
        title=text('TERBIUM',64,POS); self.reveal(title)
        unity=Group(image('unity',0.9,0.9),text('UNITY',32),text('Game Engine',21,MUTED)).arrange(DOWN,buff=0.16).move_to([-4.5,1.6,0])
        cs=VGroup(text('C#',56),text('Programming Language',21,MUTED)).arrange(DOWN,buff=0.2).move_to([-4.5,-1.6,0])
        self.play(title.animate.move_to([2,0,0])); self.reveal(unity,cs); self.play(Create(link(unity,title,POS)),Create(link(cs,title,POS))); self.pause(1); self.erase()
        editor=Rectangle(width=11.8,height=5.1,color=MUTED,stroke_width=1).move_to([0,-0.1,0])
        lib=VGroup(*(block(n,0.95,0.58) for n in ('NOT','MIN','MAX','MUL','ADD','BUF'))).arrange(DOWN,buff=0.14).move_to([-4.8,0,0])
        self.reveal(editor); self.play(LaggedStart(*(FadeIn(m) for m in lib),lag_ratio=0.12))
        caption=text('~24 ternary gates / components',31,POS).move_to([0,3.05,0]); self.reveal(caption); self.pause(0.9)
        placed=block('MUL',1.4).move_to([-1.9,0,0]); drag=text('Drag-and-drop circuit construction',31).move_to(caption)
        self.play(TransformFromCopy(lib[3],placed),ReplacementTransform(caption,drag),run_time=1.4)
        add=block('ADD',1.4).move_to([0.5,0,0]); out=block('OUT',1.4).move_to([2.9,0,0]); self.reveal(add,out)
        wires=VGroup(link(placed,add),link(add,out)); self.play(Create(wires))
        rom=block('TERNARY ROM',2.6,0.85,GOLD).move_to([0.5,1.6,0]); self.reveal(rom); self.pause(0.9)
        reusable=block('REUSABLE CIRCUIT',4,1.4).move_to([0.5,0,0])
        cap=text('Reusable / hierarchical circuits',31).move_to(drag)
        self.play(ReplacementTransform(VGroup(placed,add,out,wires),reusable),FadeOut(rom),ReplacementTransform(drag,cap),run_time=1.2); self.pause(0.8)
        pulse=Dot([-3,0,0],color=POS,radius=0.11); self.play(FadeIn(pulse)); self.play(pulse.animate.move_to([4,0,0]),run_time=1.4)
        self.play(ReplacementTransform(cap,text('Interactive ternary simulation',31,POS).move_to(cap)),FadeOut(pulse)); self.pause(0.8); self.erase()
        self.reveal(image('ui',13.5,6.5).move_to([0,0.25,0])); self.reveal(text('WORKING TERNARY LOGIC SIMULATOR',31,POS).move_to([0,-3.45,0])); self.finish()

class Slide06WorkingSimulator(Canvas):
    def construct(self):
        shot=image('ui',13.7,7.25).move_to([0,0.25,0]); self.reveal(shot)
        self.spotlight(shot,(0,0.23,0.18,0.89),'~24 TERNARY COMPONENTS',DOWN*3.55)
        self.spotlight(shot,(0.18,0.19,0.81,0.89),'DRAG & DROP   /   INTERACTIVE SIMULATION',DOWN*3.55)
        self.spotlight(shot,(0.32,0.95,0.46,0.998),'REUSABLE CIRCUITS',DOWN*3.55)
        # Extra black scan margin OUTSIDE the exact square source image.
        qr=image('qr',2.75,2.75).move_to([5.18,-1.45,0]).set_z_index(4)
        pad=Rectangle(width=3.6,height=3.6,stroke_width=0,fill_color=BLACK,fill_opacity=1).move_to(qr).set_z_index(3)
        note=text('OPEN SOURCE',25,POS).move_to([5.18,0.7,0]).set_z_index(5)
        small=text('GitHub Repository',19).move_to([5.18,-3.55,0]).set_z_index(5)
        self.play(FadeIn(pad),FadeIn(qr),FadeIn(note),FadeIn(small),run_time=1.2); self.finish(2.5)

class Slide07CircuitsBuilt(Canvas):
    def construct(self):
        cats=VGroup(text('MUX',40,POS),text('DEMUX',40,POS),text('SPECIAL CIRCUIT',38,GOLD)).arrange(RIGHT,buff=1)
        self.reveal(cats); self.pause(0.7); self.play(cats.animate.move_to([0,3.3,0]).scale(0.8))
        for category in ('mux','demux'):
            focus=0 if category=='mux' else 1
            self.play(*(cats[i].animate.set_opacity(1 if i==focus else 0.3) for i in range(3)))
            shot=None; ratio=None
            for key,caption in [(category+'3','3:1' if focus==0 else '1:3'),(category+'9','9:1' if focus==0 else '1:9'),(category+'27','27:1' if focus==0 else '1:27')]:
                new=image(key,12.7,5.8); newratio=text(caption,42,POS).move_to([0,-3.25,0])
                if shot is None: self.reveal(new,newratio)
                else: self.play(FadeOut(shot),FadeIn(new),ReplacementTransform(ratio,newratio),run_time=1.2)
                shot,ratio=new,newratio; self.pause(1.4)
            self.play(FadeOut(shot),FadeOut(ratio))
        self.play(cats[0].animate.set_opacity(0.15),cats[1].animate.set_opacity(0.15),cats[2].animate.set_opacity(1).move_to([0,0,0]).scale(1.7),run_time=1.3); self.finish()

class Slide08SpecialCircuit(Canvas):
    def construct(self):
        special=text('SPECIAL CIRCUIT',52,GOLD); self.reveal(special)
        name=text('TERNARY\nNEURAL NETWORK',56,POS).move_to([0,2.2,0]); self.play(ReplacementTransform(special,name),run_time=1.3)
        net=network().scale(0.85).move_to([0,-0.6,0]); self.play(Create(net[0]),run_time=1.5)
        self.play(LaggedStart(*(FadeIn(n) for layer in net[1:] for n in layer),lag_ratio=0.15))
        self.reveal(text('FEED-FORWARD INFERENCE',30,GOLD).move_to([0,-3.1,0])); self.finish()

class Slide09NeuronMath(Canvas):
    def construct(self):
        ys=(1.7,0,-1.7); subs=('₁','₂','₃')
        inputs=VGroup(*(mathtext(f'x{n}',46).move_to([-5.3,y,0]) for n,y in zip(subs,ys)))
        dest=Circle(0.7,color=POS,fill_color=PANEL,fill_opacity=1).move_to([4.6,0,0]); y=mathtext('y',42,POS).move_to(dest)
        self.reveal(inputs,dest,y); wires=VGroup(*(link(x,dest) for x in inputs)); self.play(Create(wires))
        weights=VGroup(*(mathtext(f'w{n}',34,GOLD).move_to([-0.7,yy*0.6+0.25,0]) for n,yy in zip(subs,ys)))
        self.reveal(weights); self.pause(1)
        products=VGroup(*(mathtext(f'x{n} × w{n}',40).move_to([-2,y,0]) for n,y in zip(subs,ys)))
        self.play(*(ReplacementTransform(VGroup(inputs[i],weights[i]),products[i]) for i in range(3)),FadeOut(wires)); self.pause(0.8)
        compact=VGroup(*(mathtext(f'x{n}w{n}',42).move_to(p) for n,p in zip(subs,products)))
        self.play(*(ReplacementTransform(a,b) for a,b in zip(products,compact))); self.pause(0.6)
        row=VGroup(*(p.copy() for p in compact)).arrange(RIGHT,buff=1.1).move_to([0,0.6,0])
        self.play(*(ReplacementTransform(a,b) for a,b in zip(compact,row)),FadeOut(dest),FadeOut(y),run_time=1.5)
        plus=VGroup(*(mathtext('+',38,GOLD).move_to((row[i].get_right()+row[i+1].get_left())/2) for i in (0,1))); self.play(Write(plus))
        sumlabel=text('SUM OF WEIGHTED INPUTS',28,MUTED).move_to([0,-1.1,0]); self.reveal(sumlabel); self.pause(1)
        z=mathtext('z = x₁w₁ + x₂w₂ + x₃w₃',43).move_to([0,0.6,0]); self.play(ReplacementTransform(VGroup(row,plus),z),FadeOut(sumlabel))
        b=mathtext('+ b',43,GOLD).next_to(z,RIGHT,buff=0.2); self.reveal(b); self.play(VGroup(z,b).animate.move_to([0,0.6,0]))
        biaslabel=text('ADD BIAS',28,GOLD).move_to([0,-1.1,0]); self.reveal(biaslabel); self.pause(1)
        zfull=mathtext('z = x₁w₁ + x₂w₂ + x₃w₃ + b',43).move_to([0,1,0]); self.play(ReplacementTransform(VGroup(z,b),zfull),FadeOut(biaslabel))
        activation=mathtext('y = f(z)',54,GOLD).move_to([0,-0.8,0]); self.play(TransformFromCopy(zfull,activation))
        activation_label=text('ACTIVATION',27,GOLD).move_to([0,-2,0])
        self.reveal(activation_label); self.pause(1.1)
        start=mathtext('y = f ( b +',56); sigma=mathtext('Σ',75,GOLD); tail=mathtext('xᵢwᵢ )',56)
        formula=VGroup(start,sigma,tail).arrange(RIGHT,buff=0.22)
        hi=mathtext('3',24,GOLD).next_to(sigma,UP,buff=0.06); lo=mathtext('i = 1',24,GOLD).next_to(sigma,DOWN,buff=0.03)
        self.play(ReplacementTransform(VGroup(zfull,activation),formula),FadeOut(activation_label),FadeIn(hi),FadeIn(lo),run_time=1.6)
        self.reveal(text('INPUT × WEIGHT → SUM → BIAS → ACTIVATION → OUTPUT',25,MUTED).move_to([0,-2.4,0])); self.finish(2)

class Slide10MathToHardware(Canvas):
    def construct(self):
        eq=VGroup(*(mathtext(s,44,col) for s,col in [('y =',INK),('f(',GOLD),('x₁w₁',INK),('+',INK),
            ('x₂w₂',INK),('+',INK),('x₃w₃',INK),('+ b',GOLD),(')',GOLD)])).arrange(RIGHT,buff=0.16)
        self.reveal(eq); self.pause(0.8); self.play(eq.animate.move_to([0,2.9,0]).scale(0.8))
        ar=architecture(); self.reveal(ar[1])
        self.play(*(TransformFromCopy(eq[j],ar[2][i]) for i,j in enumerate((2,4,6))),FadeIn(ar[3]))
        self.pause(0.7)
        self.play(TransformFromCopy(VGroup(eq[3],eq[5]),ar[4])); self.pause(0.7)
        self.play(TransformFromCopy(eq[7],ar[5])); self.pause(0.7)
        self.play(TransformFromCopy(VGroup(eq[1],eq[8]),ar[6])); self.play(Create(ar[0]),FadeIn(ar[7]))
        constraints=VGroup(text('3 INPUTS',30,POS),text('1 TRIT PER INPUT',27),text('1 TRIT PER WEIGHT',27,GOLD)).arrange(RIGHT,buff=0.75).move_to([0,-2.9,0])
        self.reveal(constraints); self.finish(2)

class Slide11OurNeuron(Canvas):
    def construct(self):
        clean=architecture().scale(0.9); self.reveal(clean); self.pause(0.6)
        shot=image('neuron',13.7,5.8).move_to([0,-0.2,0]); self.play(FadeOut(clean),FadeIn(shot),run_time=1.5)
        regions=[((0.04,0.22,0.33,0.4),'THREE INPUTS'),((0.04,0.4,0.33,0.57),'WEIGHTS'),
            ((0.43,0.21,0.53,0.59),'MULTIPLICATION'),((0.6,0.34,0.7,0.58),'ADDITION / ACCUMULATION'),
            ((0.045,0.59,0.53,0.73),'BIAS'),((0.725,0.39,0.86,0.54),'ACTIVATION / TERNARY QUANTIZATION'),
            ((0.89,0.39,0.97,0.54),'OUTPUT')]
        for region,note in regions: self.spotlight(shot,region,note)
        self.reveal(text('THE MATHEMATICAL NEURON\nBECAME A TERNARY DIGITAL CIRCUIT',32,POS).move_to([0,2.95,0])); self.finish(2)

class Slide12NeuronToNetwork(Canvas):
    def construct(self):
        one=block('TERNARY\nNEURON',2.3,1.3); self.reveal(one); net=network(); three=net[2]
        self.play(TransformFromCopy(one,three[0]),TransformFromCopy(one,three[2]),ReplacementTransform(one,three[1]))
        self.reveal(net[1],net[3]); self.play(LaggedStart(*(Create(w) for w in net[0]),lag_ratio=0.07),run_time=2.2)
        labels=VGroup(text('INPUT / BUFFER',25,MUTED).move_to([-4.8,-2.6,0]),text('3 TERNARY NEURONS',25,POS).move_to([0,-2.6,0]),text('1 TERNARY NEURON',25,POS).move_to([4.8,-2.6,0]))
        self.reveal(labels,text('3 → 3 → 1',52).move_to([0,3,0])); self.pause(1)
        signals=VGroup(*(Dot(n.get_center(),color=c,radius=0.12) for n,c in zip(net[1],(NEG,ZERO,POS)))); self.reveal(signals)
        self.play(*(signals[i].animate.move_to(three[i]) for i in range(3)),run_time=1.3)
        self.play(*(s.animate.move_to(net[3][0]) for s in signals),run_time=1.3); self.pause(0.6); self.erase()
        shot=image('network',13.4,6.5).move_to([0,-0.2,0]); self.reveal(shot)
        self.spotlight(shot,(0.06,0.32,0.15,0.46),'INPUT / BUFFER'); self.spotlight(shot,(0.33,0.08,0.45,0.81),'HIDDEN LAYER — 3 NEURONS')
        self.spotlight(shot,(0.76,0.4,0.87,0.6),'OUTPUT LAYER — 1 NEURON')
        self.reveal(text('3 → 3 → 1',40,POS).move_to([0,3.25,0]),text('FEED-FORWARD INFERENCE',26,GOLD).move_to([0,-3.6,0])); self.finish(2)

class Slide13Verification(Canvas):
    def construct(self):
        left=network().scale(0.4).move_to([-3.7,0.4,0]); right=block('TERNARY\nCIRCUIT ANN',3.8,2.2).move_to([3.7,0.4,0])
        self.reveal(left,right,text('MATHEMATICAL ANN',29).move_to([-3.7,2.4,0]),text('TERNARY CIRCUIT ANN',29,POS).move_to([3.7,2.4,0]))
        same=states(32,0.6).move_to([0,-2.2,0]); self.reveal(same,text('EQUIVALENT INPUTS',23,MUTED).move_to([0,-3.05,0]))
        tokens=VGroup(same.copy(),same.copy()); self.add(tokens)
        self.play(tokens[0].animate.move_to(left[1]).scale(0.5),tokens[1].animate.move_to(right.get_left()).scale(0.5),run_time=1.3); self.pause(0.8); self.erase()
        cell=Square(0.68,color=MUTED,fill_color=PANEL,fill_opacity=1); self.reveal(cell)
        grid=VGroup(*(cell.copy() for _ in range(25))).arrange_in_grid(5,5,buff=0.12)
        self.play(ReplacementTransform(cell,grid[0]),LaggedStart(*(TransformFromCopy(cell,g) for g in grid[1:]),lag_ratio=0.03),run_time=1.6)
        tests=text('25 TESTS',38).move_to([0,3,0]); self.reveal(tests)
        # Red cell placement is illustrative; no individual test order was supplied.
        self.play(LaggedStart(*(g.animate.set_fill(NEG if i==18 else POS,opacity=0.9).set_stroke(NEG if i==18 else POS) for i,g in enumerate(grid)),lag_ratio=0.075),run_time=3)
        fail=text('1 INCORRECT OUTPUT',25,NEG).move_to([0,-2.9,0]); self.reveal(fail); self.pause(1)
        ratio=mathtext('24 / 25',66,POS).move_to([0,0.4,0]); self.play(grid.animate.scale(0.55).move_to([-4.9,0,0]),FadeOut(tests),FadeOut(fail),FadeIn(ratio)); self.pause(0.6)
        decimal=mathtext('0.96',76,POS).move_to(ratio); self.play(ReplacementTransform(ratio,decimal)); self.pause(0.6)
        pct=text('96%',112,POS).move_to([0,0.55,0]); self.play(ReplacementTransform(decimal,pct),FadeOut(grid),run_time=1.2)
        self.reveal(text('ACCURACY OVER 25 TESTS',30).move_to([0,-0.8,0]),text('24 of 25 tested outputs matched the mathematical model.',27,MUTED).move_to([0,-2,0])); self.finish(2)

class Slide14NextCobalt(Canvas):
    def construct(self):
        tree=project_tree(); self.reveal(tree[0]); self.play(Create(tree[1]),FadeIn(tree[2]),FadeIn(tree[3]))
        done=text('v1 ✓',32,POS).move_to([-3.6,-1.4,0]); self.reveal(done); self.pause(0.8)
        self.play(tree[2].animate.set_opacity(0.25),done.animate.set_opacity(0.25),tree[3].animate.scale(1.2),run_time=1.1)
        memory=block('TERNARY MEMORY',4,1.3,GOLD).move_to([0,-2.6,0]); self.reveal(memory); self.pause(0.7); self.erase()
        memory.move_to([0,1.8,0]); q=mathtext('Q ∈ {−1, 0, +1}',40,GOLD).move_to([0,0.45,0])
        self.reveal(memory,q,text('Practical writable ternary memory element',28,MUTED).move_to([0,-0.55,0])); self.pause(1.1); self.erase()
        steps=VGroup(text('TERNARY MEMORY',40,GOLD),text('COBALT IMPLEMENTATION',40,COBALT),text('TERNARY COMPUTER',40,POS)).arrange(DOWN,buff=1).move_to([0,0.4,0]); self.reveal(steps[0])
        for a,b in zip(steps,steps[1:]): self.play(GrowArrow(Arrow(a.get_bottom(),b.get_top(),buff=0.16,color=MUTED)),FadeIn(b))
        self.reveal(text('START COBALT IMPLEMENTATION',29,COBALT).move_to([0,-2.85,0]),text('after resolving the memory architecture',24,MUTED).move_to([0,-3.45,0])); self.finish(2)

class Slide15ThankYou(Canvas):
    def construct(self):
        self.wait(0.5); s=states().move_to([0,-0.7,0])
        self.play(LaggedStart(*(FadeIn(m,shift=DOWN*0.5) for m in s),lag_ratio=0.2),run_time=1.25)
        self.play(FadeIn(text('RUBIDIUM',82).move_to([0,0.65,0])),run_time=1.1)
        self.reveal(text('THANK YOU',20,MUTED).move_to([0,-2,0])); self.finish(2)

SCENE_NAMES=['Slide01Rubidium','Slide02Trit','Slide03InsideRubidium','Slide04Progress','Slide05HowTerbiumWasMade',
 'Slide06WorkingSimulator','Slide07CircuitsBuilt','Slide08SpecialCircuit','Slide09NeuronMath','Slide10MathToHardware',
 'Slide11OurNeuron','Slide12NeuronToNetwork','Slide13Verification','Slide14NextCobalt','Slide15ThankYou']
