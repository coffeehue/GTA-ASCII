"""A continuous rear-view ASCII walk with Franklin, Michael and Trevor at Del Perro Pier."""
import argparse
from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from scenic_walk import STAGE, ease, font
from gta_scenes import neon, palm
from stylized_walk import (CANVAS, FPS, SIZE, contact_shadows, curve_path,
                           feet_by_depth, glyph_masks, grid, leg, walk_motion)

ROOT = Path(__file__).resolve().parent
DURATION = 7
LETTERS = 12


@dataclass(frozen=True)
class Walker:
    name: str
    words: str
    stride: float
    shoulder: int
    sleeve: float
    skin: tuple[str, str, str]
    fabric: tuple[str, str, str]
    pants: tuple[str, str, str, str, str, str]


FRANKLIN = Walker("franklin", "FRANKLIN:CLINTON:LOS:SANTOS", 1.14, 55, .95,
    ("#a26c50", "#643e37", "#d19a69"), ("#decfba", "#9b927d", "#fff0d4"),
    ("#424b47", "#293836", "#68786c", "#202d2d", "#393b35", "#d1d3b6"))
MICHAEL = Walker("michael", "MICHAEL:DE:SANTA:VINEWOOD", 1.25, 58, .96,
    ("#c79075", "#855755", "#f1bc97"), ("#405574", "#28334e", "#778da4"),
    ("#777a88", "#4d5364", "#a0a3aa", "#353c4d", "#2c303b", "#7e7c84"))
TREVOR = Walker("trevor", "TREVOR:PHILIPS:BLAINE:COUNTY", 1.08, 48, .32,
    ("#c69573", "#855c4c", "#f1bd8f"), ("#baac95", "#82735f", "#ded0b4"),
    ("#627880", "#415a64", "#8ea0a3", "#34454f", "#625345", "#ae9d87"))

WALKERS = (FRANKLIN, MICHAEL, TREVOR)


def sleeve_and_hand(pen, walker, shoulder, side, swing):
    x, y = shoulder
    elbow = (x + side*(6+1.7*swing), y+54-1.6*swing)
    wrist = (elbow[0]+side*(2+1.9*swing), elbow[1]+48-4.6*swing)
    skin, shade, highlight = walker.skin
    fabric, dark, light = walker.fabric

    def arm_points(t, inner, outer):
        knots = ((x,y),elbow,wrist)
        part = min(1, int(t*2))
        u = t*2-part
        first,last = knots[part:part+2]
        cx,cy = (a+(b-a)*u for a,b in zip(first,last))
        return (cx-side*inner,cy), (cx+side*outer,cy)

    top = arm_points(0,12,13)
    cuff = arm_points(walker.sleeve,10,10)
    mid = arm_points(.52,10,10)
    end = arm_points(1,7,7)
    wx,wy = wrist
    curve_path(pen, skin, [
        *top, mid[1], end[1], (wx+side*9,wy+7),
        (wx+side*4,wy+17,wx-side*5,wy+18,wx-side*8,wy+8),
        end[0],mid[0],
    ])
    pen.line((mid[1],end[1]),fill=highlight,width=3)
    pen.line(((wx-side*6,wy+4),(wx-side*4,wy+12),(wx+side*2,wy+12)),fill=shade,width=2)
    sleeve_outline = [top[0],top[1]]
    if walker.sleeve>.52:
        sleeve_outline.append(mid[1])
    sleeve_outline.extend((cuff[1],cuff[0]))
    if walker.sleeve>.52:
        sleeve_outline.append(mid[0])
    pen.polygon(sleeve_outline,fill=fabric)
    pen.line((top[1],cuff[1]),fill=light,width=2)
    pen.line(cuff,fill=dark,width=4)


def draw_head(pen, walker, dx, dy):
    skin, shade, highlight = walker.skin

    def shape(color, coords, width=None):
        coords = [tuple(v + (dx if i%2==0 else dy) for i,v in enumerate(pt)) for pt in coords]
        curve_path(pen,color,coords,width=width)

    shape(skin, [(162,140),(195,140),(196,161),(204,181),(154,181),(160,164)])
    shape(shade, [(179,146),(196,144),(197,165),(203,176),(186,173)])
    shape(skin, [(157,121),(152,124),(152,136),(156,141),(161,139)])
    shape(highlight, [(201,122),(206,124),(205,136),(201,141),(197,137)])
    if walker is TREVOR:
        shape(skin,[(155,126),(152,112,159,99,171,96),(192,88,205,104,205,120),
             (204,140,199,152,188,155),(174,156,162,151,158,143)])
        shape("#392c2b",[(154,116),(159,120),(161,136),(171,143),(185,145),
             (199,136),(204,117),(204,142),(196,153),(175,156),(161,148),(155,134)])
        shape("#c6a087",[(161,111),(168,100,183,96,195,104)],width=3)
        shape("#614e43",[(163,142),(178,151),(193,147)],width=2)
    elif walker is FRANKLIN:
        shape("#121b26",[(154,126),(153,108,160,99,174,96),(188,93,204,99,206,112),
             (208,126,202,144,199,147),(182,152,165,147,158,140)])
        shape("#494a53",[(155,117),(155,107,164,100,176,98),(190,96,201,101,204,107)],width=3)
        shape("#303441",[(158,138),(174,144),(195,144),(202,137)],width=3)
    else:
        shape("#221c24",[(151,124),(148,104,164,89,183,90),(197,89,206,99,208,111),
             (208,128,206,141,197,151),(185,157,166,152,158,145),(153,133)])
        for k in range(3):
            shape("#786150" if k == 0 else "#4d3d3a",[(153+k*4,111+k*6),
                (163+k*4,97+k*4,184+k*4,94+k*5,201+k,103+k*7)],width=3)
        shape("#746258",[(199,117),(205,123),(202,135)],width=2)


@lru_cache(maxsize=3)
def jacket(walker):
    image=Image.new("RGBA",CANVAS)
    pen=ImageDraw.Draw(image)
    base,dark,light=walker.fabric
    width=walker.shoulder
    left,right=180-width,180+width
    if walker is TREVOR:
        bottom=306
        waist=39
    elif walker is MICHAEL:
        bottom=318
        waist=45
    else:
        bottom=294
        waist=40
    curve_path(pen,base,[(154,171),(199,171),(215,180),(right,189),
        (right+8,203,right+9,216,right+5,222),
        (right-10,228),(180+waist,257),(180+waist+4,bottom-7),(193,bottom+2),
        (180,bottom-2),(161,bottom+1),(180-waist,bottom-5),(180-waist,249),
        (left+10,226),(left-4,221),(left-7,201,left-5,190,left+4,186),(144,177)])
    curve_path(pen,dark,[(201,176),(right,190),(right+5,210),(right-8,227),(180+waist,259),
        (180+waist+3,bottom-8),(197,bottom),(203,277),(199,241),(205,217),(199,195)])
    curve_path(pen,light,[(left+2,207),(left+9,192),(145,181),(155,179),(152,188),
        (137,199),(left+8,220)])
    if walker is MICHAEL:
        pen.polygon([(156,172),(174,167),(192,168),(201,173),(189,184),(168,183)],fill="#8395a7")
        pen.line([(179,190),(181,237),(180,278),(181,312)],fill="#29384f",width=3)
        pen.line([(168,302),(167,316),(181,312)],fill="#687b94",width=2)
    elif walker is FRANKLIN:
        pen.polygon([(155,173),(165,168),(192,169),(201,174),(189,183),(167,183)],fill="#a1a18a")
        pen.line([(142,283),(158,289),(187,290),(219,282)],fill="#a1987e",width=5)
        pen.line([(144,207),(163,215),(201,214),(217,206)],fill="#c7bba0",width=2)
    else:
        pen.line([(157,174),(166,180),(185,183),(200,176)],fill="#766953",width=4)
        curve_path(pen,"#9c8b73",[(151,265),(171,268),(179,279),(161,286),(144,280)])
        curve_path(pen,"#a6927b",[(145,236),(150,246),(161,245),(157,235)])
        pen.line([(141,294),(159,300),(177,298),(191,303),(219,296)],fill="#8c7e6a",width=2)
    return image


def person(walker, seconds, *, stride_gain=1):
    phase,sway,bob=walk_motion(seconds,walker.stride)
    rotation=math.cos(phase)*stride_gain
    sway *= 1 + .55*(stride_gain-1)
    image=Image.new("RGBA",CANVAS)
    pen=ImageDraw.Draw(image)
    leg_scale=.97 if walker is TREVOR else 1
    for side,foot_phase in feet_by_depth(phase):
        leg(pen,side,(180+19*side+sway,298+bob),foot_phase,
            walker is FRANKLIN,leg_scale,palette=walker.pants,sway=sway,bob=bob,
            stride_gain=stride_gain)
    base,shade,light,*_=walker.pants
    pen.polygon([(140+sway,281+bob),(219+sway,281+bob),(220+sway,317+bob),
        (199+sway,329+bob),(181+sway,319+bob),(161+sway,329+bob),(140+sway,316+bob)],fill=base)
    for x in (159+sway,200+sway):
        y=305+bob
        pen.polygon([(x-11,y-7),(x+11,y-7),(x+8,y+6),(x,y+9),(x-10,y+5)],fill=shade)
        pen.line([(x-10,y-6),(x+9,y-6),(x+7,y+4),(x,y+7),(x-8,y+4)],fill=light,width=1)
    for side in (-1,1):
        sleeve_and_hand(pen,walker,(180+side*(walker.shoulder-3)+sway*.66,201+bob-side*rotation),
                        side,side*rotation)
    draw_head(pen,walker,sway*.38,bob*.65)
    body=jacket(walker).rotate(rotation*.84,Image.Resampling.BICUBIC,center=(180,290))
    image.alpha_composite(body,(round(sway),round(bob)))
    return image


@lru_cache(maxsize=1)
def dusk_plate():
    image=Image.new("RGB",STAGE)
    pen=ImageDraw.Draw(image)
    for y in range(960):
        if y<530:
            v=y/530
            color=(round(19+143*v**2),round(19+45*v**2),round(56+39*v))
        else:
            v=(y-530)/430
            color=(round(53-23*v),round(38-11*v),round(57-17*v))
        pen.line((0,y,539,y),fill=color)
    rng=random.Random(78)
    for _ in range(100):
        x,y=rng.randrange(540),rng.randrange(15,320)
        pen.point((x,y),fill=(128,116,147))
    for x,y,width in ((36,186,170),(0,211,123),(374,166,166),(312,215,169),(42,309,210),(0,333,98)):
        pen.line((x,y,x+width,y),fill="#83546f",width=3)
    pen.ellipse((57,238,141,322),fill="#ff9b7e")
    for y in (288,299,312):
        pen.line((45,y,164,y),fill="#9f6375",width=3)
    pen.rectangle((0,441,540,611),fill="#314259")
    for y in range(452,590,8):
        x=rng.randrange(540)
        pen.line((x,y,x+rng.randrange(33,132),y),fill="#536077",width=2)
    for x,y,w in ((8,390,35),(47,413,31),(87,376,23),(117,403,38),(163,388,28),(205,426,42),
                  (459,372,23),(490,401,42)):
        pen.rectangle((x,y,x+w,477),fill="#35334c")
        for wx in range(x+6,x+w-4,8):
            for wy in range(y+9,471,11):
                if rng.random()>.58:
                    pen.rectangle((wx,wy,wx+2,wy+2),fill="#ca9b84")
    # Planks and railings run toward the same point on the horizon.
    pen.polygon([(194,513),(344,513),(540,748),(540,960),(0,960),(0,753)],fill="#494153")
    for y in [520+round((i/25)**2*450) for i in range(1,26)]:
        pen.line((0,y,540,y),fill="#302e40",width=2)
        pen.line((0,y+2,540,y+2),fill="#5e4c60",width=1)
    for x in range(-100,670,70):
        pen.line((270+(x-270)*.16,517,x,960),fill="#342d42",width=2)
    for side in (-1,1):
        for i in range(11):
            depth=(i/10)**1.8
            x=269+side*(93+218*depth)
            y=521+408*depth
            pen.line((x,y-27-28*depth,x,y),fill="#7a617d",width=3+round(4*depth))
        for y in (486,499,511):
            pen.line((269+side*92,y,269+side*315,y+377),fill="#7f6484",width=3)
    return image


def pier(t):
    scene=dusk_plate().copy()
    pen=ImageDraw.Draw(scene)
    cx,cy,r=368,326,116
    # Wheel rotation moves the gondolas and the sequence of rim lights.
    for x in (303,435):
        pen.line((x,535,cx,cy),fill="#5b5275",width=8)
        pen.line((x,535,cx,cy),fill="#9b86b0",width=2)
    pen.ellipse((cx-r,cy-r,cx+r,cy+r),outline="#b782e5",width=5)
    pen.ellipse((cx-r+8,cy-r+8,cx+r-8,cy+r-8),outline="#575a83",width=2)
    colors=((255,161,187),(255,194,109),(110,228,209),(174,150,255))
    for i in range(12):
        angle=i*math.tau/12+t*.18
        x,y=cx+r*math.cos(angle),cy+r*math.sin(angle)
        color=colors[i%len(colors)]
        pen.line((cx,cy,x,y),fill=tuple(round(v*.65) for v in color),width=2)
        pen.rounded_rectangle((x-9,y-4,x+9,y+8),radius=3,fill="#675875",outline=color,width=3)
        for fraction in (.28,.48,.68,.88):
            px=cx+(x-cx)*fraction
            py=cy+(y-cy)*fraction
            pen.ellipse((px-2.6,py-2.6,px+2.6,py+2.6),fill=color)
    pen.ellipse((cx-10,cy-10,cx+10,cy+10),fill="#ffdba9",outline="#f38fb5",width=3)
    track=[(-8,496),(53,458),(114,411),(157,394),(194,410),(232,449),(282,471),(330,454),(387,461),(454,480),(550,431)]
    curve_path(pen,"#786287",[track[0],*track[1:]],width=6)
    curve_path(pen,"#ae92ca",[(x,y-5) for x,y in track],width=3)
    for x,y in track[1:-1]:
        pen.line((x,y,x,540),fill="#65526e",width=3)
    for x,y in ((91,567),(451,574)):
        palm(pen,x,y,1.22,t,((37,39,54),(109,82,109),(67,83,102)))
    for x,y in ((62,534),(477,534)):
        for i in (-1,0,1):
            px=x+i*17
            pen.polygon([(px-10,y),(px-7,y-45),(px,y-76),(px+8,y-48),(px+10,y)],
                        fill="#48364f",outline="#e89ad1")
    neon(pen,[(70,474),(126,446),(204,428),(270,423),(337,428),(413,446),(469,474)],
         (198,116,220),5)
    pen.rounded_rectangle((128,435,412,478),radius=9,fill="#392a50",outline="#cb92df",width=2)
    # String lights down the boardwalk and reflected flecks near the entrance.
    for i in range(18):
        v=i/17
        px=58+424*v
        py=502+34*math.sin(math.pi*v)
        pen.ellipse((px-2,py-2,px+2,py+2),fill="#ecc0a1")
    rng=random.Random(92)
    for i in range(100):
        y=rng.randrange(570,920)
        x=rng.randrange(12,520)
        c=("#63496e","#806081","#4c6277")[i%3]
        pen.line((x,y,x+rng.randrange(3,22),y),fill=c,width=1)
    return scene


@lru_cache(maxsize=1)
def marquee():
    layer=Image.new("RGBA",SIZE)
    pen=ImageDraw.Draw(layer)
    pen.text((540,874),"L O S   S A N T O S",font=font(17),anchor="mm",fill="#efb7d7")
    pen.text((540,914),"D E L  P E R R O  P I E R",font=font(29),anchor="mm",fill="#ffe2f2")
    return layer


def stage(t,*,stride_gain=1):
    scene=pier(t*(1+.60*(stride_gain-1)))
    travel=ease(t/DURATION)
    cast=[]
    for i,(walker,x,ground,scale) in enumerate(zip(WALKERS,(126,269,415),(870,853,868),(.85,.88,.83))):
        x+= (269-x)*.12*travel
        ground-=31*travel
        scale*=1-.07*travel
        local_t=t*(1+.24*(stride_gain-1))+(.16,.49,.78)[i]
        phase,_,_=walk_motion(local_t,walker.stride)
        contact_shadows(ImageDraw.Draw(scene),x,ground,scale,phase,"#282536",
                        stride_gain=stride_gain)
        figure=person(walker,local_t,stride_gain=stride_gain)
        sole=298+211*(.97 if walker is TREVOR else 1)+13
        layer=Image.new("RGBA",STAGE)
        layer.alpha_composite(figure.resize(tuple(round(s*scale) for s in CANVAS),Image.Resampling.LANCZOS),
                              (round(x-180*scale),round(ground-sole*scale)))
        cast.append((walker,layer))
    return scene,cast


def frame(t):
    cell=(round(LETTERS*.62),LETTERS)
    cols,rows,yy,xx,noise=grid(cell)
    chars,masks=glyph_masks(cell)
    scene,layers=stage(t)
    cast=[(walker,np.asarray(layer.resize((cols,rows),Image.Resampling.BOX))) for walker,layer in layers]
    back=np.asarray(scene.resize((cols,rows),Image.Resampling.BOX),dtype=np.float32)
    rgb=255*np.power(back/255,.66)*.86
    ramp=".:;+=*#%@"
    levels=np.clip((np.max(rgb,axis=2)/23+noise*.7).astype(np.intp),0,len(ramp)-1)
    symbols=np.array([chars.index(c) for c in ramp])[levels]
    silhouette=np.maximum.reduce([front[...,3] for _,front in cast])
    shadow=Image.fromarray(silhouette).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    rgb*=1-np.asarray(shadow)[...,None]*(.48/255)
    for walker,front in cast:
        body=front[...,3]>105
        words=np.array([chars.index(c) for c in walker.words])
        symbols[body]=words[(xx+2*yy)%len(words)][body]
        face=255*np.power(front[...,:3].astype(np.float32)/255,.66)+np.array([22,18,23])
        left=body & ~np.roll(body,1,axis=1)
        right=body & ~np.roll(body,-1,axis=1)
        face[left]=face[left]*.67+np.array([252,194,172])*.33
        face[right]=face[right]*.76+np.array([146,187,240])*.24
        rgb[body]=np.minimum(255,face[body])
    tiled=(masks[symbols][...,None]*rgb[:,:,None,None,:]).astype(np.uint8)
    tiled=tiled.transpose(0,2,1,3,4).reshape(rows*cell[1],cols*cell[0],3)
    output=Image.new("RGB",SIZE)
    output.paste(Image.fromarray(tiled),((SIZE[0]-tiled.shape[1])//2,(SIZE[1]-tiled.shape[0])//2))
    output.paste(marquee(),mask=marquee().getchannel("A"))
    return output


def export(path):
    import imageio_ffmpeg

    if path.exists():
        raise FileExistsError(path)
    writer=imageio_ffmpeg.write_frames(str(path),SIZE,fps=FPS,codec="libx264",
        pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=1,
        output_params=["-crf","15","-preset","medium","-movflags","+faststart"])
    writer.send(None)
    try:
        for i in range(DURATION*FPS):
            writer.send(np.asarray(frame(i/FPS)))
    finally:
        writer.close()


def preview(fullscreen):
    import tkinter as tk
    from time import perf_counter
    from PIL import ImageTk

    window=tk.Tk()
    window.title("GTA V ASCII | Del Perro Pier")
    window.configure(bg="black")
    window.attributes("-fullscreen",fullscreen)
    height=min(window.winfo_screenheight()-(0 if fullscreen else 95),
               round(window.winfo_screenwidth()*16/9))
    display_size=(round(height*9/16),height)
    label=tk.Label(window,bg="black",bd=0)
    label.pack(expand=True)
    window.bind("<Escape>",lambda _:window.destroy())
    start=perf_counter()

    def tick():
        now=perf_counter()
        picture=frame((now-start)%DURATION)
        label.image=ImageTk.PhotoImage(picture.resize(display_size,Image.Resampling.LANCZOS))
        label.configure(image=label.image)
        window.after(max(1,33-round((perf_counter()-now)*1000)),tick)

    tick()
    window.mainloop()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fullscreen",action="store_true")
    parser.add_argument("--export",type=Path)
    args=parser.parse_args()
    if args.export:
        export(args.export)
    else:
        preview(args.fullscreen)
