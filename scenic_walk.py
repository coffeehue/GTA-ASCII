"""Render the Tommy and CJ ASCII walk cycles in their respective game settings."""
import argparse
from functools import lru_cache
import math
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

from stylized_walk import FPS, SIZE, character, contact_shadows, glyph_masks, grid, motion

from gta_scenes import SIZE as STAGE, ease, font, los_santos, vice_city

ROOT = Path(__file__).resolve().parent

SHOT = 5
LENGTH = SHOT * 2


@lru_cache(maxsize=1)
def alley_reference():
    images = []
    for texture in ("sky", "brick", "asphalt"):
        path = ROOT / "assets" / f"san-andreas-{texture}.png"
        with Image.open(path) as image:
            images.append(image.convert("RGB"))
    return tuple(images)


def bicycle(pen, x, y, scale):
    """Side view of the parked BMX, with distinct wheels and an open frame."""
    def point(u, v):
        return x + u * scale, y + v * scale

    def line(points, fill, width):
        pen.line([point(*p) for p in points], fill=fill,
                 width=max(1, round(width*scale)), joint="curve")

    pen.ellipse((*point(-64, -3), *point(68, 8)), fill="#3b3029")
    centers = ((-45, -22), (44, -24))
    for u, v in centers:
        box = (*point(u-23,v-24), *point(u+23,v+24))
        pen.ellipse(box, fill="#473a2e", outline="#23202b", width=round(8*scale))
        pen.ellipse((*point(u-19,v-20), *point(u+19,v+20)),
                    outline="#d9d2aa", width=max(3, round(3.6*scale)))
        for i in range(9):
            angle = i*math.tau/9
            line(((u,v), (u+19*math.cos(angle),v+20*math.sin(angle))), "#6d7063", 1)
        pen.ellipse((*point(u-3,v-3), *point(u+3,v+3)), fill="#c2c6ac")
    for points in (
        ((-45,-22),(-23,-53),(2,-27),(-45,-22)),
        ((-23,-53),(28,-55),(2,-27)),
        ((29,-55),(44,-24)),
    ):
        line(points,"#182a32",9)
        line(points,"#82e0cf",6)
    line(((-26,-62),(-23,-53)), "#c8c8aa", 4)
    line(((-36,-64),(-16,-65)), "#232129", 7)
    line(((28,-56),(25,-72),(33,-78),(43,-76)), "#acbeb1", 4)
    line(((37,-78),(46,-76)), "#302d34", 6)
    line(((2,-27),(9,-19),(18,-19)), "#d0c1a2", 3)
    line(((-44,-21),(2,-25)), "#aaa494", 2)
    line(((-43,-54),(-49,-53)), "#d9785d", 5)


def san_andreas(t, duration=SHOT):
    scene, _ = los_santos(t)
    sky, brick, asphalt = alley_reference()
    scene.paste(sky, (0, 0))
    # The reference has a high orange wall on the right and a shorter brick wall on the left.
    pen = ImageDraw.Draw(scene)
    pen.polygon([(0,520),(244,458),(287,457),(540,642),(540,960),(0,960)], fill="#5b4834")
    road = Image.new("RGB", STAGE)
    road.paste(ImageEnhance.Brightness(asphalt).enhance(.82), (0,505))
    road_mask = Image.new("L", STAGE)
    ImageDraw.Draw(road_mask).polygon([(0,739),(241,483),(285,482),(540,778),(540,960),(0,960)], fill=255)
    scene.paste(road,(0,0),road_mask)

    left = [(0,324),(244,447),(244,502),(0,746)]
    right = [(287,437),(540,152),(540,842),(287,499)]
    pen.polygon(left,fill="#94734f",outline="#a98358",width=3)
    pen.polygon(right,fill="#744b36",outline="#a16944",width=3)
    detail = Image.new("RGB", STAGE)
    detail.paste(brick.resize((275,420),Image.Resampling.BILINEAR),(0,330))
    brick_mask = Image.new("L",STAGE)
    ImageDraw.Draw(brick_mask).polygon([(0,548),(244,477),(244,502),(0,746)],fill=150)
    scene.paste(detail,(0,0),brick_mask)
    for a,b,c,d in (left,right):
        for row in range(1,12):
            v=row/12
            y0=a[1]+(d[1]-a[1])*v
            y1=b[1]+(c[1]-b[1])*v
            color="#604731" if a[0]==0 else "#573d2f"
            pen.line((a[0],y0,b[0],y1),fill=color,width=2)
            for column in range(1,10):
                u=(column-(.5 if row%2 else 0))/10
                u=u**(1.55 if a[0]==0 else .66)
                x=a[0]+(b[0]-a[0])*u
                y=y0+(y1-y0)*u
                height=((d[1]-a[1])*(1-u)+(c[1]-b[1])*u)/12
                pen.line((x,y,x,y-height),fill=color,width=1)
    pen.line(((0,548),(244,477)),fill="#c09462",width=4)
    pen.line(((287,467),(540,398)),fill="#b27950",width=4)
    pen.line(((287,499),(540,842)),fill="#b07a50",width=2)
    # Draw the moving foreground over a fixed bike in the alley.
    approach = ease(t/duration)
    bicycle(pen,399 + 17*approach,665 + 38*approach,1.02 + .17*approach)
    rng=random.Random(8)
    for _ in range(42):
        x=rng.randrange(540)
        y=rng.randrange(753,950)
        pen.line((x,y,x+rng.randrange(2,12),y),fill="#7e6248",width=1)
    return scene, None


def ocean_drive(t):
    scene, sign = vice_city(t*.82)
    pen = ImageDraw.Draw(scene)
    for y in range(253):
        v = y / 252
        pen.line((0,y,540,y), fill=(round(32+64*v*v),round(29+16*v),round(65+27*v)))
    pen.ellipse((48,123,139,214),fill="#db8e94")
    for y,width,x in ((145,133,13),(157,186,32),(181,151,9),(200,161,45),(216,217,3)):
        pen.line((x,y,x+width,y),fill="#765273",width=3)
    return scene, sign


def stage(name,t,duration=SHOT,*,stride_gain=1):
    tommy = name == "tommy"
    world_t = t*(1+.42*(stride_gain-1))
    shot,sign = ocean_drive(world_t) if tommy else san_andreas(world_t,duration)
    # Both figures remain full body, roughly half the height of the portrait.
    approach = ease(t / duration)
    x = (231+22*approach if tommy else 224+34*approach)
    ground = (840-25*approach if tommy else 848-35*approach)
    scale = (.99-.10*approach if tommy else 1.02-.10*approach)
    walk_t=t*(1+.24*(stride_gain-1))
    phase,_,_=motion(name,walk_t)
    contact_shadows(ImageDraw.Draw(shot),x,ground,scale,phase,
                    "#100e20" if tommy else "#332b24",stride_gain=stride_gain)
    figure = character(name,walk_t,leg_scale=.91 if tommy else 1,stride_gain=stride_gain)
    width,height=figure.size
    sole = (297 + 211*(.91 if tommy else 1) + 13)
    actor = Image.new("RGBA",STAGE)
    actor.alpha_composite(figure.resize((round(width*scale),round(height*scale)),Image.Resampling.LANCZOS),
                         (round(x-180*scale),round(ground-sole*scale)))
    return shot, actor, sign


def frame(name,t,letters=14,*,fade=True,duration=SHOT):
    cell=(round(letters*.62),letters)
    cols,rows,yy,xx,noise=grid(cell)
    backdrop,actor,sign=stage(name,t,duration)
    back=np.asarray(backdrop.resize((cols,rows),Image.Resampling.BOX),dtype=np.float32)
    front=np.asarray(actor.resize((cols,rows),Image.Resampling.BOX))
    body=front[...,3]>104
    chars,masks=glyph_masks(cell)
    # Dense punctuation carries the scenery, while readable names define the figures.
    ramp=".:;+=*#%@"
    back_gain=.89 if name=="tommy" else .83
    rgb=255*np.power(back/255,.63)*back_gain
    brightness=np.max(rgb,axis=2)
    levels=np.clip((brightness/24+noise*.9).astype(np.intp),0,len(ramp)-1)
    symbols=np.array([chars.index(c) for c in ramp])[levels]
    word="TOMMY:VERCETTI:VICE:CITY" if name=="tommy" else "CARL:JOHNSON:GROVE:STREET"
    actor_ids=np.array([chars.index(c) for c in word])[(xx+yy*2)%len(word)]
    symbols[body]=actor_ids[body]
    front_rgb=255*np.power(front[...,:3].astype(np.float32)/255,.84)+np.array([11,13,16])
    rim=body & ~np.roll(body,1,axis=1)
    rim_color=(144,235,219) if name=="tommy" else (227,169,109)
    front_rgb[rim]=front_rgb[rim]*.73+np.array(rim_color)*.27
    rgb[body]=np.minimum(255,front_rgb[body])
    if fade:
        rgb *= min(1, .54 + t*6, .54+(duration-t)*6)
    tiled=(masks[symbols][...,None]*rgb[:,:,None,None,:]).astype(np.uint8)
    tiled=tiled.transpose(0,2,1,3,4).reshape(rows*cell[1],cols*cell[0],3)
    output=Image.new("RGB",SIZE)
    output.paste(Image.fromarray(tiled),((SIZE[0]-tiled.shape[1])//2,(SIZE[1]-tiled.shape[0])//2))
    if sign:
        draw=ImageDraw.Draw(output)
        x,y=sign
        draw.text((x*2,y*2),"O C E A N   V I E W",font=font(31),anchor="mm",fill="#ffd1ef")
        draw.text((x*2,y*2+25),"H O T E L",font=font(16),anchor="mm",fill="#88ded8")
    return output


def shot_at(t):
    return ("tommy",t) if t<SHOT else ("cj",t-SHOT)


def export(path):
    import imageio_ffmpeg
    if path.exists():
        raise FileExistsError(path)
    writer=imageio_ffmpeg.write_frames(str(path),SIZE,fps=FPS,codec="libx264",
        pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=1,
        output_params=["-crf","15","-preset","medium","-movflags","+faststart"])
    writer.send(None)
    try:
        for i in range(LENGTH*FPS):
            writer.send(np.asarray(frame(*shot_at(i/FPS))))
    finally:
        writer.close()


def preview(fullscreen):
    import tkinter as tk
    from time import perf_counter
    from PIL import ImageTk

    window=tk.Tk()
    window.title("GTA ASCII | Vice City and San Andreas")
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
        picture=frame(*shot_at((now-start)%LENGTH))
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
