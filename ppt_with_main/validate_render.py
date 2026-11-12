"""Render actual animation beats and create review contact sheets."""
from pathlib import Path
import os, json, argparse
from manim import tempconfig
import rubidium as deck
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--snapshots-only',action='store_true')
    parser.add_argument('--slides',nargs='+',type=int)
    args=parser.parse_args()
    os.environ['RUBIDIUM_CAPTURE']='1'
    out=ROOT/'review15'; out.mkdir(exist_ok=True)
    issues=[]; records=[]
    with tempconfig({'pixel_width':960,'pixel_height':540,'frame_rate':10,
        'media_dir':str(ROOT/'media_review15'),'disable_caching':True,
        'save_last_frame':args.snapshots_only,'write_to_movie':not args.snapshots_only,
        'progress_bar':'none','verbosity':'WARNING'}):
        for n in (args.slides or range(1,16)):
            name=deck.SCENE_NAMES[n-1]; print('REVIEW '+name,flush=True)
            with tempconfig({'output_file':name}):
                scene=getattr(deck,name)(); scene.render()
            for beat in scene.beats:
                for b in beat['bounds']:
                    if b[0]<-7.08 or b[1]>7.08 or b[2]<-3.95 or b[3]>3.95:
                        issues.append({'scene':name,'time':beat['time'],'bounds':b})
            records.append({'scene':name,'duration':scene.time})
            files=sorted(out.glob(name+'_*.png'))
            sheet=Image.new('RGB',(1440,290*((len(files)+2)//3)),deck.BG)
            draw=ImageDraw.Draw(sheet)
            for i,p in enumerate(files):
                with Image.open(p) as im: sheet.paste(im.convert('RGB').resize((480,270)),((i%3)*480,(i//3)*290))
                draw.text(((i%3)*480+8,(i//3)*290+272),p.stem,fill='white')
            sheet.save(out/(name+'_contact.jpg'))
    (out/'validation.json').write_text(json.dumps({'records':records,'safe_area_issues':issues},indent=2))
    print(f'Safe-area issues: {len(issues)}',flush=True)
    if issues: raise SystemExit(1)
if __name__=='__main__': main()
