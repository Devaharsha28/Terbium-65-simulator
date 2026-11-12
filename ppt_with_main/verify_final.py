"""Inspect encoded outputs and capture real movie frames for final visual QA."""
from pathlib import Path
import json, subprocess, hashlib
from PIL import Image, ImageDraw
from rubidium import ROOT,SCENE_NAMES,BG
FFMPEG='D:/ffmpeg/bin/ffmpeg.exe'
FFPROBE='D:/ffmpeg/bin/ffprobe.exe'
def probe(path):
    return json.loads(subprocess.check_output([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(path)]))
def capture(path,t,out):
    subprocess.run([FFMPEG,'-v','error','-y','-ss',str(t),'-i',str(path),'-frames:v','1',str(out)],check=True)
def main():
    out=ROOT/'review15'/'encoded'; out.mkdir(exist_ok=True)
    records=[]; elapsed=0; errors=[]
    for index,name in enumerate(SCENE_NAMES):
        clip=ROOT/'media'/'videos'/'rubidium'/'1080p30'/(name+'.mp4')
        p=probe(clip); stream=next(s for s in p['streams'] if s['codec_type']=='video')
        duration=float(p['format']['duration'])
        if (stream['width'],stream['height'],stream['r_frame_rate'])!=(1920,1080,'30/1'):
            errors.append(name+' format mismatch')
        records.append({'scene':index+1,'name':name,'start':round(elapsed,3),'duration':duration})
        elapsed+=duration
        metadata=json.loads((ROOT/'review15'/(name+'.json')).read_text())
        beats=metadata['beats']
        frames=[]
        for i,b in enumerate(beats):
            target=out/f'{name}_{i+1:02}.png'
            capture(clip,min(duration-0.25,max(0,b['time']*duration/metadata['duration']-0.25)),target); frames.append(target)
        # Inspect a frame inside a movement, in addition to stable final compositions.
        target=out/f'{name}_motion.png'; capture(clip,duration*0.45,target); frames.append(target)
        sheet=Image.new('RGB',(1440,290*((len(frames)+2)//3)),BG); draw=ImageDraw.Draw(sheet)
        for i,f in enumerate(frames):
            with Image.open(f) as im: sheet.paste(im.convert('RGB').resize((480,270)),((i%3)*480,(i//3)*290))
            draw.text(((i%3)*480+5,(i//3)*290+272),f.stem,fill='white')
        sheet.save(out/(name+'_contact.jpg'))
    movie=probe(ROOT/'Rubidium.mp4'); actual=float(movie['format']['duration'])
    if abs(actual-elapsed)>0.1: errors.append('Joined movie duration mismatch')
    pairs=[('C:/Users/Deva/Pictures/'+f,ROOT/'assets'/f) for f in ('27mux.png','27demux.png','neuron.png','network.png','terbium ui.png')]
    pairs += [('C:/Users/Deva/Downloads/'+f,ROOT/'assets'/f) for f in ('terbium-tRsAWc.png','download.png')]
    for original,copy in pairs:
        if hashlib.sha256(Path(original).read_bytes()).digest()!=hashlib.sha256(copy.read_bytes()).digest():
            errors.append(copy.name+' source mismatch')
    finalframes=sorted(out.glob('Slide*_*.png'))
    with Image.open(ROOT/'assets'/'terbium-tRsAWc.png') as qr:
        if qr.width!=qr.height: errors.append('QR is not square')
    (ROOT/'scene_timing.json').write_text(json.dumps(records,indent=2))
    (out/'validation.json').write_text(json.dumps({'scenes':15,'seconds':actual,'format':'1920x1080 / 30 fps',
        'source_images_identical':not any('mismatch' in e for e in errors),'errors':errors},indent=2))
    print(json.dumps({'scenes':15,'seconds':actual,'errors':errors}))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
