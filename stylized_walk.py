"""Stylized rear-view GTA character art, animated and rendered with ASCII."""
from pathlib import Path
import argparse
from functools import lru_cache
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ascii_glyphs import SIZE, atlas

ROOT = Path(__file__).resolve().parent
CANVAS = (360, 640)
FPS = 30
SHOT = 3.5


def curve_path(pen, color, points, *, width=None):
    """Draw a path made from points and cubic Bezier segments."""
    path = [points[0]]
    for point in points[1:]:
        if len(point) == 2:
            path.append(point)
            continue
        x0, y0 = path[-1]
        x1, y1, x2, y2, x3, y3 = point
        for step in range(1, 13):
            t = step / 12
            u = 1 - t
            path.append((u**3*x0 + 3*u*u*t*x1 + 3*u*t*t*x2 + t**3*x3,
                         u**3*y0 + 3*u*u*t*y1 + 3*u*t*t*y2 + t**3*y3))
    if width is None:
        pen.polygon(path, fill=color)
    else:
        pen.line(path, fill=color, width=width, joint="curve")


def motion(name, seconds):
    return walk_motion(seconds, 1.12 if name == "tommy" else 1.25,
                       2.2 if name == "tommy" else 2.8)


def walk_motion(seconds, period, sway_width=2.4):
    phase = math.tau * seconds / period
    sway = -sway_width * math.sin(phase)
    bob = 1.35 * math.cos(2 * phase)
    return phase, sway, bob


def step_sample(phase):
    """Return projected ground position, toe clearance, and heel rise."""
    cycle = phase / math.tau % 1
    stance = .62
    if cycle < stance:
        travel = cycle / stance
        heel = 3.2 * max(0, (travel - .78) / .22) ** 2
        return -9 + 18 * travel, 0, heel
    swing = (cycle - stance) / (1 - stance)
    progress = swing * swing * (3 - 2 * swing)
    return 9 - 18 * progress, 10 * math.sin(math.pi * swing) ** 1.2, 3.2 * (1 - swing)**4


def feet_by_depth(phase):
    feet = ((-1, phase), (1, phase + math.pi))
    return sorted(feet, key=lambda foot: step_sample(foot[1])[0])


def arm(pen, side, shoulder, swing, cj):
    sx, sy = shoulder
    spread = 6 + 1.5 * swing
    ex, ey = sx + side * spread, sy + 57 - 1.5*swing
    wx, wy = ex + side * (2 + 1.7*swing), ey + 50 - 4.5*swing
    skin = "#9a513b" if cj else "#d78d60"
    shadow = "#583139" if cj else "#98524e"
    light = "#d78a5b" if cj else "#ffc18c"
    rim = "#d7a071" if cj else "#ffa890"
    upper = 14 if cj else 11

    def at(x, y, u, v):
        return x + side*u, y+v

    def seg(*points):
        return tuple(v for point in points for v in point)

    p = lambda u,v: at(sx,sy,u,v)
    q = lambda u,v: at(ex,ey,u,v)
    r = lambda u,v: at(wx,wy,u,v)
    curve_path(pen, skin, [
        p(-upper, -4), seg(p(-9,-20),p(11,-16),p(upper,1)),
        seg(p(upper+4,25),q(12,-24),q(9,-2)),
        seg(q(12,19),r(9,-15),r(8,1)),
        seg(r(13,9),r(8,19),r(0,20)),
        seg(r(-9,18),r(-10,12),r(-7,0)),
        seg(r(-8,-18),q(-12,14),q(-9,-1)),
        seg(q(-12,-20),p(-upper-1,19),p(-upper,-4)),
    ])
    curve_path(pen, shadow, [
        p(-upper,-2), q(-3,-14), q(-4,5), r(-3,1), r(1,19), r(-6,17),
        r(-8,7), r(-6,-5), q(-9,2), q(-11,-12), p(-upper,-2),
    ])
    curve_path(pen, light, [
        p(3,-9), seg(p(15,-1),p(12,24),q(6,-10)),
        seg(q(1,-11),p(4,18),p(0,3)),
    ])
    curve_path(pen, light, [q(4,3),seg(q(9,15),r(5,-11),r(5,-3)),r(0,-6),q(4,3)])
    curve_path(pen, rim, [p(upper,3),seg(p(upper+1,17),q(9,-15),q(9,-6))],width=2)
    curve_path(pen, shadow, [r(8,6),r(2,9),r(1,15)],width=2)
    if side == -1 and not cj:
        curve_path(pen, "#f4bf76", [r(-6,-3),r(0,-1),r(7,-3)],width=3)


def leg(pen, side, hip, phase, cj, length_scale=1, *,
        palette=None, stripe=None, cargo=False, sway=0, bob=0, stride_gain=1):
    sx, sy = hip
    depth, lift, heel = step_sample(phase)
    depth *= stride_gain
    lift *= 1 + (stride_gain-1)*.62
    # The planted foot stays under its lane while the pelvis shifts over it.
    ankle = (sx - sway + side * (6 - lift*.15),
             sy - bob + 211*length_scale + depth - lift - heel)
    knee = ((sx + ankle[0])*.5 + side*(1 + lift*.24),
            sy + 103*length_scale + .39*depth - .62*lift - .2*heel)
    a, b = knee
    x, y = ankle
    wide = 18 if cj else 16
    cuff = 13 if cj else 11
    shade = "#273e64" if cj else "#27536c"
    base = "#456894" if cj else "#467f9b"
    lit = "#7396b5" if cj else "#76aaba"
    deep = "#192f4e"
    sole = "#c1c6bd" if cj else "#e3ecde"
    shoe = "#313e48" if cj else "#748c8f"
    if palette is not None:
        base, shade, lit, deep, shoe, sole = palette
    curve_path(pen, sole, [
        (x-cuff,y-5),(x+cuff,y-5),
        (x+cuff+3,y+3,x+cuff+2,y+10,x+8,y+11),
        (x+2,y+13,x-cuff-5,y+12,x-cuff-5,y+8),(x-cuff,y-5),
    ])
    curve_path(pen, shoe, [
        (x-cuff,y-5),(x+cuff,y-4),
        (x+cuff+2,y+1,x+cuff+2,y+4,x+9,y+6),(x-cuff-3,y+7),(x-cuff-3,y+3),
    ])
    curve_path(pen, base, [
        (sx-wide,sy-11),(sx+wide,sy-13),
        (sx+wide+6,sy+12,a+14,b-17,a+14,b),
        (a+15,b+25,x+cuff,y-20,x+cuff,y),
        (x+8,y+4,x-6,y+5,x-cuff,y+2),
        (x-cuff-2,y-13,a-13,b+20,a-14,b),
        (a-16,b-18,sx-wide-5,sy+12,sx-wide,sy-11),
    ])
    curve_path(pen, shade, [
        (sx-8,sy-7),(sx+wide,sy-13),(a+13,b-9),(a+13,b+18),(x+cuff,y),
        (x+1,y+3),(x+5,y-21),(a+3,b+8),(a-2,b-8),
    ])
    curve_path(pen, lit, [(sx-wide+3,sy+6),(a-10,b-17),(a-11,b+3),(x-12,y-16)],width=2)
    curve_path(pen, deep, [(a-8,b-1),(a+1,b+3),(a+9,b+1)],width=2)
    curve_path(pen, lit, [(x-11,y-10),(x-1,y-7),(x+7,y-8)],width=2)
    curve_path(pen, shade, [(x-12,y-4),(x-4,y),(x+5,y-2)],width=2)
    if stripe:
        curve_path(pen, stripe, [(sx+side*(wide-3),sy+8),(a+side*12,b),
                                 (x+side*(cuff-2),y-4)],width=3)
    if cargo:
        px = (sx+a)/2 + side*7
        py = (sy+b)/2
        curve_path(pen, shade, [(px-9,py-13),(px+9,py-13),(px+8,py+13),
                               (px,py+17),(px-8,py+13)])
        curve_path(pen, lit, [(px-8,py-12),(px+8,py-12),(px+6,py-7),
                             (px-7,py-7)],width=2)


def contact_shadows(pen, x, ground, scale, phase, fill, *, stride_gain=1):
    for side, foot_phase in feet_by_depth(phase):
        depth, lift, _ = step_sample(foot_phase)
        if lift > 3:
            continue
        cx = x + side * 25 * scale
        cy = ground + depth * scale * stride_gain
        pen.ellipse((cx-14*scale,cy-2*scale,cx+14*scale,cy+3*scale),fill=fill)


def palm_print(pen, x, y, angle, size, color):
    def pt(u, v):
        return (x + size*(u*math.cos(angle)-v*math.sin(angle)),
                y + size*(u*math.sin(angle)+v*math.cos(angle)))
    curve_path(pen, color, [pt(-1,12),pt(0,5),pt(0,0)],width=max(1,round(size*1.5)))
    for side in (-1, 1):
        for i in range(4):
            tip = side*(11-i*1.6)
            curve_path(pen, color, [pt(0,i*.6),(*pt(tip*.43,-9+i*2),*pt(tip*.8,-9+i*2),*pt(tip,-4+i*3)),
                     (*pt(tip*.55,-4+i*1.9),*pt(tip*.21,-2+i*.6),*pt(0,2+i*.6))])


@lru_cache(maxsize=2)
def torso(name):
    out = Image.new("RGBA", CANVAS)
    pen = ImageDraw.Draw(out)
    cj = name == "cj"
    if cj:
        # The neck and shoulders form the base under the tank's scoop and straps.
        curve_path(pen, "#a76147", [(164,157),(195,154),(205,171),(230,180),(249,200),
            (239,240),(227,254),(222,287),(220,315),(141,316),(138,277),(128,244),
            (111,218),(116,192),(139,181),(157,173)])
        curve_path(pen,"#d68c62",[(160,171),(165,181),(153,198),(123,207),(116,203),(133,183)])
        curve_path(pen,"#763c35",[(195,162),(205,174),(230,182),(245,196),(232,215),(209,197)])
        curve_path(pen,"#ebe6cf",[(140,181),(153,176),(164,193,187,205,208,175),(224,180),
            (223,204,226,219,238,235),(226,257,220,278,223,311),
            (203,322,167,322,139,312),(140,284,135,254,125,238),
            (136,217,140,201,140,181)])
        curve_path(pen,"#a9b8b1",[(217,180),(224,180),(226,216,231,225,238,235),
            (225,260,222,284,223,311),(209,320),(207,299),(212,267),(213,246),
            (216,221),(215,201)])
        curve_path(pen,"#fff1d8",[(145,184),(152,181),(159,191,177,204,194,195)],width=3)
        curve_path(pen,"#fbf4df",[(143,217),(152,206),(174,211),(187,207),(206,201),
            (204,218),(193,227),(180,231),(153,229),(138,237)])
        curve_path(pen,"#c3c8b5",[(140,280),(157,285),(177,284),(195,278),(207,279)],width=3)
        curve_path(pen,"#f8ecd2",[(142,306),(173,312),(199,307),(217,304)],width=3)
    else:
        shirt = [(157,174),(199,173),(211,178),(229,184,247,185,253,203),
                 (260,219,262,238,258,250),(232,256),(225,246),
                 (219,272,230,290,226,318),(199,329),(179,316),
                 (158,325),(131,320),(131,288,135,267,130,244),
                 (122,253),(103,247),(107,219,109,199,121,190),(146,182)]
        curve_path(pen,"#42c6b7",shirt)
        curve_path(pen,"#237a81",[(207,181),(235,187),(250,195),(258,218),(258,247),(236,252),
            (226,245),(222,269),(226,301),(223,318),(203,324),(204,301),(197,276),(203,246),
            (199,226),(203,204)])
        curve_path(pen,"#79e5c5",[(112,217),(115,200),(132,190),(152,184),(156,190),(138,198),
            (130,212),(119,237),(108,243)])
        motif = Image.new("RGBA",CANVAS)
        m = ImageDraw.Draw(motif)
        for x,y,angle,s in [(137,201,-.68,1.0),(167,210,.40,1.23),(201,196,-.52,.91),
                            (227,212,.51,1.18),(118,234,-.8,.86),(154,248,.49,1.26),
                            (189,243,-.54,1.42),(246,240,.76,.89),(212,268,.6,1.15),
                            (150,284,-.42,1.17),(183,278,.45,1.20),(199,307,-.38,1.09),
                            (140,313,-.51,.84),(174,311,.62,.89)]:
            palm_print(m,x,y,angle,s,"#16585f")
        alpha = np.minimum(np.asarray(motif.getchannel("A")),
                           np.asarray(out.getchannel("A")))
        motif.putalpha(Image.fromarray(alpha))
        out.alpha_composite(motif)
        curve_path(pen,"#266e75",[(156,174),(171,169),(198,171),(208,181),(194,187),(168,187),(150,181)])
        curve_path(pen,"#9ef2ce",[(156,175),(171,173),(190,174),(200,177)],width=2)
        curve_path(pen,"#20717d",[(104,245),(117,250),(127,248)],width=4)
        curve_path(pen,"#56a9aa",[(236,248),(247,245),(257,243)],width=3)
        curve_path(pen,"#a8ead1",[(133,280),(135,296),(134,311)],width=2)
        curve_path(pen,"#df81a2",[(252,205),(258,223),(259,243)],width=2)
    # Keep the shoulder line fixed and shorten the shirt/tank toward the waist.
    scale = .84
    shoulder_y = 180
    return out.transform(CANVAS,Image.Transform.AFFINE,
        (1,0,0,0,1/scale,shoulder_y*(1-1/scale)),Image.Resampling.BICUBIC)


def head(pen, name, hx, hy):
    def shape(color, coords, width=None):
        shifted = [tuple(v+(hx if i%2==0 else hy) for i,v in enumerate(point)) for point in coords]
        curve_path(pen,color,shifted,width=width)
    cj = name == "cj"
    shape("#a86449" if cj else "#d69064",[
        (161,143),(197,143),(198,163,200,172,206,177),
        (193,190,165,189,155,176),(162,165,161,154,161,143)])
    shape("#75413a" if cj else "#a45d51",[(183,146),(197,143),(198,164),(204,175),(195,182),(184,180)])
    shape("#a66c53" if cj else "#cc8d69",[(155,123),(152,126),(152,136),(156,143),(162,143),(161,126)])
    shape("#b47a57" if cj else "#e5a87e",[(201,122),(207,123),(208,131),(205,141),(200,143)])
    if cj:
        shape("#141b27",[(155,125),(152,110,160,96,174,92),
            (190,88,205,95,207,108),(209,120,205,137,202,146),
            (192,151,171,152,160,145),(156,137),(155,125)])
        shape("#39414b",[(156,118),(154,108,162,97,176,94),
            (187,91,198,95,202,102),(184,98),(173,100),(162,109)])
        shape("#56545a",[(157,126),(157,112,162,102,174,98)],width=2)
        shape("#242a32",[(174,141),(188,143),(201,139),(200,146),(188,151),(174,148)])
    else:
        shape("#241a24",[(154,129),(148,123),(148,109),(155,96),
            (163,86,182,82,196,88),(207,94,211,106,209,121),(206,132,204,143,197,151),
            (190,157,168,156,161,149),(156,144),(154,129)])
        shape("#49302d",[(151,112),(156,98,168,91,183,90),(198,88,204,100,205,107),
            (193,100,177,99,166,107),(161,112),(158,129),(154,127)])
        for i in range(4):
            shape("#a36d57" if i==0 else "#604038",
                [(156+i*4,109+i*4),(164+i*4,95+i*3,186+i*4,91+i*4,201+i,100+i*5)],width=3)
        shape("#563832",[(205,113),(203,133,202,142,191,151)],width=2)
        shape("#a66e5d",[(149,111),(150,103),(154,97)],width=2)


def character(name, seconds, *, leg_scale=1, stride_gain=1):
    phase, sway, bob = motion(name, seconds)
    rotation = math.cos(phase) * stride_gain
    sway *= 1 + .55*(stride_gain-1)
    cj = name == "cj"
    canvas = Image.new("RGBA", CANVAS)
    pen = ImageDraw.Draw(canvas)
    for side, foot_phase in feet_by_depth(phase):
        leg(pen,side,(180+side*19+sway,297+bob),foot_phase,cj,leg_scale,
            sway=sway,bob=bob,stride_gain=stride_gain)
    curve_path(pen,"#335579" if cj else "#396780",
               [(142+sway,281+bob),(218+sway,281+bob),(220+sway,315+bob),
                (199+sway,329+bob),(181+sway,317+bob),(161+sway,328+bob),(140+sway,315+bob)])
    for side in (-1,1):
        x = 180 + side*19 + sway
        y = 305 + bob
        curve_path(pen,"#223d57",[(x-13,y-7),(x+12,y-9),(x+11,y+6),(x,y+12),(x-12,y+6)])
        curve_path(pen,"#82a9ad",[(x-11,y-6),(x+10,y-8),(x+9,y+5),(x,y+10),(x-10,y+5)],width=1)
    for side in (1,-1):
        arm(pen,side,(180+side*(54 if cj else 59)+sway*.66,204+bob-side*rotation),
            side*rotation,cj)
    body = torso(name).rotate(.85*rotation if cj else .72*rotation,
                             Image.Resampling.BICUBIC,center=(180,291))
    face = Image.new("RGBA", CANVAS)
    head(ImageDraw.Draw(face),name,sway*.38,8+bob*.65)
    canvas.alpha_composite(face)
    canvas.alpha_composite(body,(round(sway),round(bob)))
    return canvas


@lru_cache(maxsize=4)
def grid(cell):
    cols, rows = SIZE[0]//cell[0], SIZE[1]//cell[1]
    yy,xx = np.indices((rows,cols))
    noise = ((xx*37+yy*71+xx*yy*3)%113)/113
    return cols,rows,yy,xx,noise


@lru_cache(maxsize=4)
def glyph_masks(cell):
    chars, tiles = atlas(cell)
    expanded = np.stack([
        np.asarray(Image.fromarray(tile).filter(ImageFilter.MaxFilter(3)))
        for tile in tiles
    ])
    # Add weight around the thin strokes, with clear gaps between glyphs.
    masks = np.maximum(tiles, expanded * .43).astype(np.float32) / 255
    return chars, masks


def frame(name,t,letters=14,*,transition=True):
    cell=(round(letters*.62),letters)
    cols,rows,yy,xx,noise=grid(cell)
    img=character(name,t)
    # Start close on the hair and clothes, then reveal the stride and both feet.
    progress = min(1, max(0, (t-.12)/1.08)) if transition else 1
    ease = progress*progress*(3-2*progress)
    zoom = 1 + .23*(1-ease)
    span_x, span_y = 286/zoom, 509/zoom
    center_y = 256 + 34.5*ease
    shot=img.transform((cols,rows),Image.Transform.AFFINE,
        (span_x/cols,0,180-span_x/2,0,span_y/rows,center_y-span_y/2),Image.Resampling.BICUBIC)
    pixels=np.asarray(shot)
    chars,tiles=glyph_masks(cell)
    word="TOMMY VERCETTI VICE CITY" if name=="tommy" else "CARL JOHNSON GROVE STREET"
    ids=np.array([chars.index(c) if c!=" " else chars.index(":") for c in word])
    symbols=ids[(xx+yy*2)%len(ids)]
    active=pixels[...,3]>123
    rgb=pixels[...,:3].astype(np.float32)
    rgb=np.minimum(255,255*np.power(rgb/255,.85)+np.array([11,13,16],dtype=np.float32))
    left_edge = active & ~np.roll(active, 1, axis=1)
    right_edge = active & ~np.roll(active, -1, axis=1)
    left_light = (140,228,219) if name=="tommy" else (214,163,110)
    right_light = (221,114,158) if name=="tommy" else (117,170,138)
    rgb[left_edge] = rgb[left_edge]*.70 + np.array(left_light)*.30
    rgb[right_edge] = rgb[right_edge]*.77 + np.array(right_light)*.23
    if transition:
        # Keep the subject visible from frame one. The cut breaks into letters briefly.
        age=abs(t-0.10)
        if t<.20:
            symbols=np.where(noise>.46, chars.index("+"), symbols)
            rgb*= (.76+.24*min(1,age/.1))
        if t>SHOT-.21:
            decay=(t-(SHOT-.21))/.21
            active &= noise>.82*decay
            symbols=np.where(noise<decay*.74,chars.index("/"),symbols)
    rgb*=active[...,None]
    tiles=tiles[symbols][...,None]*rgb[:,:,None,None,:]
    tiled=tiles.astype(np.uint8).transpose(0,2,1,3,4).reshape(rows*cell[1],cols*cell[0],3)
    image=Image.new("RGB",SIZE)
    image.paste(Image.fromarray(tiled),((SIZE[0]-tiled.shape[1])//2,(SIZE[1]-tiled.shape[0])//2))
    return image


def name_at(seconds, character_name):
    if character_name != "both":
        return character_name
    return "tommy" if seconds % (2*SHOT) < SHOT else "cj"


def export(path,character_name,letters):
    import imageio_ffmpeg
    if path.exists():
        raise FileExistsError(f"{path} exists. Choose another export path.")
    frames=round(FPS*SHOT*(2 if character_name=="both" else 1))
    writer=imageio_ffmpeg.write_frames(str(path), SIZE, fps=FPS, codec="libx264",
        pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=1,
        output_params=["-crf","14","-preset","medium","-movflags","+faststart"])
    writer.send(None)
    try:
        for i in range(frames):
            t=i/FPS
            writer.send(np.asarray(frame(name_at(t,character_name),t%SHOT,letters)))
    finally:
        writer.close()


def preview(character_name, letters, fullscreen):
    import time
    import tkinter as tk
    from PIL import ImageTk
    root=tk.Tk()
    root.title("GTA ASCII | Tommy & CJ")
    root.configure(bg="black")
    root.attributes("-fullscreen",fullscreen)
    height=min(root.winfo_screenheight()-(0 if fullscreen else 95),
               round(root.winfo_screenwidth()*16/9))
    size=(round(height*9/16),height)
    label=tk.Label(root,bg="black",bd=0)
    label.pack(expand=True)
    state={"name":character_name,"t":0.0,"paused":False,"last":time.perf_counter()}

    def tick():
        now=time.perf_counter()
        if not state["paused"]:
            state["t"]+=now-state["last"]
        state["last"]=now
        t=state["t"]
        name=state["name"]
        local=t%SHOT if name=="both" else t
        picture=frame(name_at(t,name),local,letters,transition=name=="both")
        label.image=ImageTk.PhotoImage(picture.resize(size,Image.Resampling.LANCZOS))
        label.configure(image=label.image)
        root.after(max(1,33-round((time.perf_counter()-now)*1000)),tick)

    for key,name in zip("123",("tommy","cj","both")):
        root.bind(key,lambda _,name=name: state.update(name=name,t=0.0))
    root.bind("<space>",lambda _:state.update(paused=not state["paused"]))
    root.bind("<Escape>",lambda _:root.destroy())
    tick()
    root.mainloop()


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--character", choices=["tommy","cj","both"], default="both")
    parser.add_argument("--letters", type=int, choices=[10,12,14,16], default=14)
    parser.add_argument("--fullscreen",action="store_true")
    parser.add_argument("--export",type=Path)
    parser.add_argument("--stills",action="store_true")
    args=parser.parse_args()
    if args.stills:
        for name in ("tommy","cj"):
            frame(name,1.6,args.letters,transition=False).save(ROOT/f"{name}-stylized-ascii.png")
    elif args.export:
        export(args.export,args.character,args.letters)
    else:
        preview(args.character,args.letters,args.fullscreen)
