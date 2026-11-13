"""GTA III and IV rear-view walks, animated in colored ASCII."""
import argparse
from functools import lru_cache
import math
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from gta5_pier import Walker, sleeve_and_hand
from scenic_walk import STAGE, ease, font
from gta_scenes import neon
from stylized_walk import (CANVAS, FPS, SIZE, contact_shadows, curve_path,
                           feet_by_depth, glyph_masks, grid, leg, walk_motion)

DURATION = 6
NIKO = Walker("niko","NIKO:BELLIC:LIBERTY:CITY",1.26,57, .97,
    ("#3f4850","#282b34","#617078"),("#a27c55","#655040","#cca878"),
    ("#3c526f","#293c5b","#697f9b","#20304c","#444039","#8d7b65"))
CLAUDE = Walker("claude","CLAUDE:PORTLAND:LIBERTY:CITY",1.14,54,.95,
    ("#bb8465","#825746","#d4a07f"),("#353d45","#232a33","#676971"),
    ("#78855a","#4c5940","#a7af75","#394933","#242a2c","#6e7470"))
CAST = {"gta3": CLAUDE, "gta4": NIKO}


@lru_cache(maxsize=2)
def coat(walker):
    image = Image.new("RGBA", CANVAS)
    pen = ImageDraw.Draw(image)
    base,dark,light = walker.fabric
    w = walker.shoulder
    left,right = 180-w,180+w
    curve_path(pen,base,[(155,170),(204,170),(219,179),(right,192),
        (right+9,204,right+8,217,right+2,227),(right-11,232),
        (223,254),(226,290),(216,309),(144,309),(134,297),(137,259),
        (left+11,233),(left-4,225),(left-8,208,left-5,198,left+1,192),(144,181)])
    curve_path(pen,dark,[(201,180),(224,185),(right,195),(right+5,216),(224,230),
        (214,248),(217,274),(225,289),(218,302),(199,300),(200,274),(194,248),(198,225)])
    curve_path(pen,light,[(left,211),(left+2,199),(142,187),(160,181),(166,188),
        (153,198),(145,214),(139,237),(131,225)])
    curve_path(pen,light,[(144,260),(148,274),(143,290),(154,294)],width=3)
    curve_path(pen,dark,[(151,232),(157,255),(155,278),(161,285)],width=3)
    curve_path(pen,light,[(143,296),(163,300),(194,301),(215,297)],width=3)
    if walker is NIKO:
        # Wide, turned-up collar and caramel panels from the supplied reference.
        curve_path(pen,"#c8ac7f",[(152,182),(149,163),(158,155),(165,160),
            (179,168),(194,165),(205,155),(212,163),(214,181),(194,191),(166,191)])
        curve_path(pen,"#7a6047",[(154,165),(166,176),(183,180),(203,173),
            (210,162),(211,178),(194,187),(168,187)])
        curve_path(pen,"#e2c396",[(152,163),(157,157),(170,165),(182,170)],width=3)
        curve_path(pen,"#77583f",[(143,272),(149,292),(145,302),(165,307),(164,288),(158,280)])
        pen.line([(190,210),(188,251),(188,287)],fill="#846344",width=2)
        pen.line([(151,307),(174,308),(213,307)],fill="#564336",width=4)
    else:
        pen.rounded_rectangle((155,168,205,185),radius=5,fill="#252d34",outline="#68717b",width=2)
        pen.line([(144,205),(158,209),(182,212),(204,210),(220,204)],fill="#667079",width=2)
        pen.line([(143,301),(163,305),(194,305),(218,301)],fill="#202931",width=7)
        pen.line([(144,300),(170,302),(215,300)],fill="#566068",width=2)
    return image


def character(walker, t, *, stride_gain=1):
    is_niko = walker is NIKO
    phase,sway,bob = walk_motion(t,walker.stride)
    rotation = math.cos(phase)*stride_gain
    sway *= 1 + .55*(stride_gain-1)
    layer = Image.new("RGBA",CANVAS)
    pen = ImageDraw.Draw(layer)
    for side,foot_phase in feet_by_depth(phase):
        leg(pen,side,(180+19*side+sway,298+bob),foot_phase,
            not is_niko, .98 if is_niko else 1, palette=walker.pants,
            stripe="#a5a9a4" if is_niko else None, cargo=not is_niko,
            sway=sway,bob=bob,stride_gain=stride_gain)
    pen.polygon([(140+sway,292+bob),(219+sway,292+bob),(218+sway,320+bob),
                 (198+sway,329+bob),(180+sway,322+bob),(160+sway,329+bob),(140+sway,318+bob)],
                 fill=walker.pants[0])
    for side in (-1,1):
        sleeve_and_hand(pen,walker,(180+side*(walker.shoulder-4)+sway*.66,202+bob-side*rotation),
                        side,side*rotation)
    hx,hy = 180+sway*.38,132+bob*.65
    pen.polygon([(hx-19,hy+8),(hx+16,hy+9),(hx+23,hy+48),(hx-23,hy+48)],fill="#ba876c")
    pen.ellipse((hx-28,hy-5,hx-17,hy+13),fill="#af7b66")
    pen.ellipse((hx+18,hy-5,hx+27,hy+13),fill="#c9957b")
    if is_niko:
        curve_path(pen,"#302620",[(hx-25,hy-1),(hx-28,hy-26,hx-16,hy-38,hx,hy-38),
            (hx+21,hy-40,hx+30,hy-24,hx+24,hy-3),
            (hx+21,hy+14,hx+13,hy+22,hx,hy+22),(hx-15,hy+22,hx-24,hy+11,hx-25,hy-1)])
        curve_path(pen,"#705540",[(hx-25,hy-9),(hx-25,hy-23,hx-18,hy-31,hx-6,hy-34)],width=3)
        pen.line([(hx-13,hy+12),(hx+3,hy+16),(hx+17,hy+10)],fill="#574033",width=3)
    else:
        curve_path(pen,"#211b1c",[(hx-25,hy+1),(hx-29,hy-17),(hx-21,hy-32),
            (hx-12,hy-31),(hx-4,hy-43),(hx+12,hy-36),(hx+27,hy-26),
            (hx+24,hy-3),(hx+20,hy+16),(hx+4,hy+22),(hx-15,hy+17)])
        curve_path(pen,"#705649",[(hx-25,hy-12),(hx-17,hy-24,hx-8,hy-31,hx+8,hy-34)],width=3)
        curve_path(pen,"#483933",[(hx-17,hy+9),(hx-5,hy+15),(hx+14,hy+13)],width=3)
    layer.alpha_composite(coat(walker).rotate(rotation*.85,Image.Resampling.BICUBIC,center=(180,291)),
                         (round(sway),round(bob)))
    return layer


def sky(warm):
    scene=Image.new("RGB",STAGE)
    pen=ImageDraw.Draw(scene)
    for y in range(960):
        glow=math.exp(-((y-477)/210)**2)
        color=(round(26+64*glow),round(29+53*glow),round(48+26*glow)) if warm else (
               round(28+76*glow),round(40+77*glow),round(57+71*glow))
        pen.line((0,y,539,y),fill=color)
    return scene


def skyline(pen,seed,horizon,cool):
    rng=random.Random(seed)
    x=0
    while x<540:
        w=rng.randrange(15,45)
        height=rng.randrange(42,190)
        top=horizon-height
        pen.rectangle((x,top,x+w,horizon),fill="#415464" if cool else "#302e40")
        pen.rectangle((x+w//4,top-7,x+w*3//4,top+3),fill="#495b68" if cool else "#383648")
        for px in range(x+5,x+w-2,7):
            for py in range(top+8,horizon-6,9):
                if rng.random()>.64:
                    pen.rectangle((px,py,px+2,py+3),fill="#7d8480" if cool else "#c29e7d")
        x+=w+3


def road(pen,t,cool):
    van=267
    pen.polygon([(van-42,509),(van+42,509),(550,780),(550,960),(-5,960),(-5,780)],
                fill="#3a4750" if cool else "#3e394b")
    for side in (-1,1):
        color="#71868f" if cool else "#b08f95"
        pen.line((van+side*47,509,van+side*380,960),fill=color,width=5)
        pen.line((van+side*56,511,van+side*418,960),fill="#374551",width=3)
    for i in range(10):
        v=(i/10+t*.052)%1
        y=520+v**2*440
        w=1+7*v
        pen.line((van-w,y,van+w,y+5+v*21),fill="#b4a780" if cool else "#947982",width=2)
    rng=random.Random(91)
    for i in range(96):
        v=(rng.random()+t*.039)%1
        y=543+v**2*418
        x=van+(rng.random()-.5)*(126+570*v)
        c=("#71665b","#6a7880","#52636d") if cool else ("#80628a","#596787","#9c777a")
        pen.line((x,y,x+2+v*19,y),fill=c[i%3],width=1+int(v*2))


@lru_cache(maxsize=1)
def junction_plate():
    scene=sky(True)
    pen=ImageDraw.Draw(scene)
    skyline(pen,13,520,False)
    for x,y,w,front in ((0,143,112,"#252e42"),(100,232,63,"#303247"),(163,333,45,"#403944"),
                        (411,173,129,"#30283e"),(362,256,55,"#383346"),(328,349,43,"#373b53")):
        pen.polygon([(x,y),(x+w,y+36),(x+w,562),(x,594)],fill=front,outline="#555169")
        for row in range(y+65,551,17):
            for px in range(x+9,x+w-5,13):
                if (px+row)%11>3:
                    pen.rectangle((px,row,px+6,row+7),fill="#69576c")
    return scene


def star_junction(t):
    scene=junction_plate().copy()
    pen=ImageDraw.Draw(scene)
    road(pen,t,False)
    # The billboard canyon gives way to the street and the yellow taxis.
    boards=((8,232,114,378,"#c24b51"),(126,346,192,418,"#3d96ac"),(430,225,532,368,"#466fb9"),
            (377,320,427,432,"#9a5daa"),(426,387,531,446,"#bd6b42"))
    for i,(x,y,r,b,c) in enumerate(boards):
        pen.rectangle((x,y,r,b),fill=c,outline="#e6c3a3",width=3)
        for line in range(y+9,b-6,8):
            p=(line*3+i*7+int(t*13))%(r-x-9)
            pen.line((x+5,line,x+5+p,line),fill="#e3a987" if i in (0,4) else "#9cafd9",width=2)
    pen.rounded_rectangle((115,182,391,230),radius=6,fill="#332f52",outline="#a689bd",width=3)
    for index in range(10):
        x=148+index*25
        pen.polygon([(x,653),(x+9,653),(x+12,676),(x-3,676)],fill="#8d8591")
    for x,c in ((84,"#795768"),(151,"#956757"),(370,"#626a92"),(448,"#78618b")):
        for i in range(12):
            v=(i/12+t*.06)%1
            y=580+331*v*v
            start=267+(x-267)*(.35+.85*v)
            pen.line((start,y,start+17+29*v,y),fill=c,width=2+int(2*v))
    for x,y in ((17,565),(97,539),(432,545),(523,592)):
        pen.line((x,y,x,y-89),fill="#747890",width=4)
        neon(pen,[(x-10,y-89),(x+10,y-89)],(255,206,139),4)
    car_x=342+38*ease(t/DURATION)
    car_y=593+21*ease(t/DURATION)
    pen.polygon([(car_x-34,car_y),(car_x-19,car_y-17),(car_x+16,car_y-17),
                 (car_x+31,car_y),(car_x+38,car_y+19),(car_x-35,car_y+19)],
                 fill="#bc813d",outline="#eac17e")
    pen.rectangle((car_x-15,car_y-13,car_x+13,car_y-4),fill="#454755")
    pen.rectangle((car_x-9,car_y-24,car_x+8,car_y-18),fill="#edd194")
    neon(pen,[(car_x+21,car_y+9),(car_x+30,car_y+9)],(238,100,90),3)
    return scene


@lru_cache(maxsize=1)
def bridge_plate():
    scene=sky(False)
    pen=ImageDraw.Draw(scene)
    pen.ellipse((62,186,137,261),fill="#d6dcbd")
    skyline(pen,23,506,True)
    pen.rectangle((0,507,539,607),fill="#495e6c")
    rng=random.Random(55)
    for _ in range(98):
        x,y=rng.randrange(540),rng.randrange(510,608)
        pen.line((x,y,x+rng.randrange(8,38),y),fill="#70818a",width=1)
    return scene


def callahan(t):
    scene=bridge_plate().copy()
    pen=ImageDraw.Draw(scene)
    road(pen,t,True)
    # Draw the distant span first so the nearer steelwork overlaps it cleanly.
    for cx,base,top,half in ((274,551,313,41),(271,692,174,142)):
        inner=half*.79
        near=half>60
        steel="#7c5b4d" if near else "#6a5d54"
        shadow="#53433e" if near else "#4b4948"
        edge="#ad8c72" if near else "#86796b"
        width=24 if near else 11
        rise=base-top
        for side in (-1,1):
            reach=(322-inner) if near else (202-inner)
            drop=298 if near else 152
            cable=[(cx+side*(inner+reach*u/32),top+drop*(u/32)**1.4)
                   for u in range(33)]
            for i in range(4,32,4):
                x,y=cable[i]
                pen.line((x,y,x,base+i*3),fill=steel,width=3 if near else 2)
            pen.line(cable,fill=shadow,width=9 if near else 5)
            pen.line(cable,fill=edge,width=4 if near else 2)
        for y in (top+13,top+59,top+107):
            offset=inner+(half-inner)*(y-top)/rise
            pen.line((cx-offset,y,cx+offset,y),fill=shadow,width=11 if near else 6)
            pen.line((cx-offset,y-2,cx+offset,y-2),fill=edge,width=3 if near else 2)
        if near:
            for x in range(cx-round(inner),cx+round(inner)-30,36):
                pen.line((x,top+15,x+36,top+58),fill=steel,width=5)
                pen.line((x+36,top+15,x,top+58),fill=steel,width=5)
        for side in (-1,1):
            x=cx+side*half
            head=cx+side*inner
            pen.line((x,base,head,top),fill=shadow,width=width)
            pen.line((x-side*3,base,head-side*3,top),fill=steel,width=width-7 if near else width-3)
            inset=7 if near else 3
            pen.line((x-side*inset,base,head-side*inset,top),fill=edge,width=4 if near else 2)
    for side in (-1,1):
        for i in range(10):
            v=(i/9)**1.5
            x=270+side*(52+269*v)
            y=542+342*v
            pen.line((x,y-24-33*v,x,y),fill="#827d70",width=3+int(v*3))
        pen.line((270+side*52,518,270+side*318,828),fill="#454b4e",width=8)
        pen.line((270+side*52,517,270+side*318,827),fill="#958e7b",width=3)
    pen.rounded_rectangle((160,259,380,296),radius=3,fill="#334b46",outline="#908e78",width=3)
    return scene


@lru_cache(maxsize=2)
def signage(game):
    layer=Image.new("RGBA",SIZE)
    p=ImageDraw.Draw(layer)
    if game=="gta4":
        p.text((507,412),"S T A R   J U N C T I O N",font=font(27),anchor="mm",fill="#f1d5ee")
        p.text((124,559),"CNT",font=font(49),anchor="mm",fill="#ffe1ca")
        p.text((963,534),"WHIZ",font=font(36),anchor="mm",fill="#d9f3ff")
    else:
        p.text((540,551),"C A L L A H A N   B R I D G E",font=font(22),anchor="mm",fill="#d6e1bf")
    return layer


def stage(game,t,*,stride_gain=1):
    is_niko=game=="gta4"
    walker=CAST[game]
    world_t=t*(1+.52*(stride_gain-1))
    background=star_junction(world_t) if is_niko else callahan(world_t)
    travel=ease(t/DURATION)
    x=(250 if is_niko else 268)+13*travel
    ground=864-36*travel
    scale=.96-.06*travel
    local=t*(1+.24*(stride_gain-1))
    phase,_,_=walk_motion(local,walker.stride)
    contact_shadows(ImageDraw.Draw(background),x,ground,scale,phase,"#2d3542",
                    stride_gain=stride_gain)
    actor=Image.new("RGBA",STAGE)
    figure=character(walker,local,stride_gain=stride_gain)
    sole=298+211*(.98 if is_niko else 1)+13
    actor.alpha_composite(figure.resize(tuple(round(v*scale) for v in CANVAS),Image.Resampling.LANCZOS),
                         (round(x-180*scale),round(ground-sole*scale)))
    return background,actor


def frame(game,t):
    is_niko=game=="gta4"
    walker=CAST[game]
    background,actor=stage(game,t)
    cell=(8,13)
    cols,rows,yy,xx,noise=grid(cell)
    back=np.asarray(background.resize((cols,rows),Image.Resampling.BOX),dtype=np.float32)
    front=np.asarray(actor.resize((cols,rows),Image.Resampling.BOX))
    alpha=front[...,3]
    body=alpha>102
    chars,masks=glyph_masks(cell)
    rgb=255*np.power(back/255,.66)*(.88 if is_niko else .82)
    ramp=".:;+=*#%@"
    levels=np.clip((np.max(rgb,axis=2)/24+noise*.7).astype(np.intp),0,len(ramp)-1)
    symbols=np.array([chars.index(c) for c in ramp])[levels]
    shade=Image.fromarray(alpha).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.1))
    rgb*=1-np.asarray(shade)[...,None]*(.46/255)
    words=np.array([chars.index(c) for c in walker.words])
    symbols[body]=words[(xx+yy*2)%len(words)][body]
    figure_rgb=255*np.power(front[...,:3].astype(np.float32)/255,.65)+np.array([18,17,23])
    edge=body & ~np.roll(body,1,axis=1)
    rim=np.array([255,187,139] if is_niko else [175,215,226])
    figure_rgb[edge]=figure_rgb[edge]*.57+rim*.43
    rgb[body]=np.minimum(255,figure_rgb[body])
    tiled=(masks[symbols][...,None]*rgb[:,:,None,None,:]).astype(np.uint8)
    tiled=tiled.transpose(0,2,1,3,4).reshape(rows*cell[1],cols*cell[0],3)
    image=Image.new("RGB",SIZE)
    image.paste(Image.fromarray(tiled),((SIZE[0]-tiled.shape[1])//2,(SIZE[1]-tiled.shape[0])//2))
    sign=signage(game)
    image.paste(sign,mask=sign.getchannel("A"))
    return image


def export(game,path):
    import imageio_ffmpeg

    if path.exists():
        raise FileExistsError(path)
    writer=imageio_ffmpeg.write_frames(str(path),SIZE,fps=FPS,codec="libx264",
        pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=1,
        output_params=["-crf","15","-preset","medium","-movflags","+faststart"])
    writer.send(None)
    try:
        for i in range(DURATION*FPS):
            writer.send(np.asarray(frame(game,i/FPS)))
    finally:
        writer.close()


def preview(game,fullscreen):
    import tkinter as tk
    from time import perf_counter
    from PIL import ImageTk

    window=tk.Tk()
    window.title("Liberty City | GTA III and IV ASCII")
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
        picture=frame(game,(now-start)%DURATION)
        label.image=ImageTk.PhotoImage(picture.resize(display_size,Image.Resampling.LANCZOS))
        label.configure(image=label.image)
        window.after(max(1,33-round((perf_counter()-now)*1000)),tick)

    tick()
    window.mainloop()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game",choices=CAST)
    parser.add_argument("--fullscreen",action="store_true")
    parser.add_argument("--export",type=Path)
    args=parser.parse_args()
    if args.export:
        export(args.game,args.export)
    else:
        preview(args.game,args.fullscreen)
