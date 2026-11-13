"""The GTA ASCII reel and individual game clips."""
import argparse
from functools import lru_cache, partial
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import gta5_pier
import gta6_keys_walk
import gta_evolution
import liberty_city_walk
import scenic_walk
from ascii_glyphs import atlas as glyph_tiles
from gta_scenes import display_font
from scenic_walk import STAGE, ease, font
from stylized_walk import SIZE, glyph_masks

ROOT = Path(__file__).resolve().parent
CELL = (9, 15)
COLS, ROWS = SIZE[0] // CELL[0], SIZE[1] // CELL[1]
DETAIL_CELL = (6, 10)
DETAIL_GRID = (SIZE[0] // DETAIL_CELL[0], SIZE[1] // DETAIL_CELL[1])
GAME_NAMES = ("gta3", "vice-city", "san-andreas", "gta4", "gta5", "gta6")
GAME_LABELS = ("GTA III", "GTA Vice City", "GTA San Andreas", "GTA IV", "GTA V", "GTA VI")
FINAL_DURATIONS = (5, 5, 5, 5, 5, 6)
SHORT_DURATIONS = (3, 3, 3, 3, 3, 4)
CLIP_DURATION = 6
STRIDE = 1.66
LABEL_POSITION = (72, 280)
OPENING_COPY_SECONDS = 4
PORTRAIT_SIZES = {1080: SIZE, 1440: (1440, 2560)}
PHONE_DURATIONS = (5,) * len(GAME_NAMES)

# Channel balance and moving accents for each location.
COLOR = (
    ((.79,1.12,1.24), (85,166,191)),    # Callahan Bridge
    ((1.20,.94,1.26), (235,91,188)),    # Ocean Drive
    ((1.18,1.08,.81), (210,158,78)),    # Los Santos alley
    ((1.05,.94,1.28), (153,119,233)),   # Star Junction
    ((1.23,.97,1.12), (243,124,163)),   # Del Perro
    ((1.24,1.09,1.22), (100,232,228)),  # Leonida Keys
)

# Give each top its own hue. Jeans stay cool while the skin and hair use
# the original character colors.
TOP_BALANCE = {
    "CLAUDE": (.86, .94, 1.03),
    "TOMMY": (.68, 1.15, 1.12),
    "CARL": (1.09, 1.06, 1.03),
    "NIKO": (1.13, .91, .77),
    "FRANKLIN": (1.10, 1.04, .85),
    "MICHAEL": (.78, 1.00, 1.23),
    "TREVOR": (1.11, 1.00, .82),
    "JASON": (1.09, 1.07, .99),
    "LUCIA": (.90, .98, 1.19),
}

def draw_scene(index, time, duration):
    if index in (0,3):
        game = "gta3" if index==0 else "gta4"
        scene,layer = liberty_city_walk.stage(game,time,stride_gain=STRIDE)
        words = liberty_city_walk.CAST[game].words
        return scene,[(words,layer)],liberty_city_walk.signage(game)
    if index in (1,2):
        name = "tommy" if index==1 else "cj"
        scene,layer,sign = scenic_walk.stage(name,time,duration,stride_gain=STRIDE)
        words = "TOMMY:VERCETTI:VICE:CITY" if index==1 else "CARL:JOHNSON:GROVE:STREET"
        label = Image.new("RGBA",SIZE)
        if sign:
            x,y = (2*value for value in sign)
            pen = ImageDraw.Draw(label)
            pen.text((x,y),"O C E A N   V I E W",font=font(31),anchor="mm",fill="#ffd6f3")
            pen.text((x,y+24),"H O T E L",font=font(18),anchor="mm",fill="#a3f9f0")
        return scene,[(words,layer)],label
    if index==4:
        scene,layers = gta5_pier.stage(time,stride_gain=STRIDE)
        return scene,[(walker.words,layer) for walker,layer in layers],gta5_pier.marquee()
    scene,layers = gta6_keys_walk.stage(time,stride_gain=STRIDE,cast_spacing=11)
    cast=[("LUCIA:CAMINOS:LEONIDA" if lucia else "JASON:DUVAL:LEONIDA",layer)
          for lucia,layer in layers]
    return scene,cast,gta6_keys_walk.sign()


@lru_cache(maxsize=2)
def sample_geometry(dimensions=(COLS,ROWS)):
    cols,rows=dimensions
    row,col=np.indices((rows,cols))
    rng=np.random.default_rng(119)
    grain=rng.random((rows,cols),dtype=np.float32)
    accents=rng.random((38,4))
    return row,col,grain,accents


def moving_details(scene,index,time):
    """Move highlights toward the camera as the walkers advance."""
    _,_,_,accents=sample_geometry()
    base=np.asarray(COLOR[index][1])
    pen=ImageDraw.Draw(scene)
    for distance, lane, rate, phase in accents:
        z=(distance+time*(.075+.075*rate))%1
        depth=z*z
        y=553+depth*394
        side=-1 if lane<.5 else 1
        offset=(95+182*abs(lane-.5))*depth
        x=270+side*(30+offset)+math.sin(time*1.8+phase*math.tau)*4
        shine=.33+.30*math.sin(math.pi*z)**2
        if index in (4,5):
            # Reflections on the pier and water travel across the planks and ripples.
            x+=math.sin(time*1.5+phase*math.tau)*14
            length=3+30*depth
            end=(x+length,y)
        else:
            # The road and sidewalk marks move along their perspective lines.
            end=(x+side*(3+6*depth),y+3+15*depth)
        color=tuple(int(value*shine) for value in base)
        pen.line(((x,y),end),fill=color,width=1+int(depth>.57))


def camera(time,duration,index):
    progress=ease(time/duration)
    direction=-1 if index%2 else 1
    zoom=1.025+.115*progress
    x=270+direction*(progress-.45)*19+2.1*math.sin(time*1.55)
    y=662+3.2*math.sin(time*2.15)
    left=x-x/zoom
    top=y-y/zoom
    return 1/zoom,left,top


def grid_sample(image, view, dimensions=(COLS,ROWS)):
    zoom,left,top=view
    cols,rows=dimensions
    matrix=(STAGE[0]*zoom/cols,0,left,0,STAGE[1]*zoom/rows,top)
    return np.asarray(image.transform(dimensions,Image.Transform.AFFINE,matrix,
                                     Image.Resampling.BICUBIC),dtype=np.float32)


def grade(rgb, balance, saturation, gamma):
    lifted=np.power(rgb/255,gamma)
    luminance=lifted[...,0]*.2126+lifted[...,1]*.7152+lifted[...,2]*.0722
    saturated=luminance[...,None]+(lifted-luminance[...,None])*saturation
    return np.clip(saturated*np.asarray(balance)*255,0,255)


def backdrop_colors(back, balance, index, row):
    rgb = grade(back,balance,1.65,.78 if index==0 else .72)
    if index == 5:
        # Warm up the coral sunset and color the cooler surfaces separately.
        sky = row < row.shape[0]*.49
        water = (row > row.shape[0]*.43) & (back[...,2] > back[...,0]*1.32)
        rgb[sky] = np.minimum(255,rgb[sky]*np.array([1.12,.98,1.13])+[13,0,4])
        rgb[water] = np.minimum(255,rgb[water]*np.array([.80,1.19,1.23])+[0,11,6])
    return rgb


def character_colors(layer, body, words, accent, row):
    raw = layer[...,:3]
    name = words.partition(":")[0]
    paint = grade(raw,(1.07,1.03,1.09),1.46,.47)
    occupied = row[body]
    if occupied.size == 0:
        return paint
    relative_y = (row - occupied.min()) / max(1, int(np.ptp(occupied)))
    red, green, blue = raw.transpose(2,0,1)
    skin = (red > 88) & (red > green*1.16) & (red > blue*1.23)
    head = body & (relative_y < .182)
    hair = head & (red < 130) & ~skin
    # Hold the hair's deeper tones instead of lifting them like clothing.
    paint[hair] = grade(raw[hair],(.95,.97,1.03),1.17,.67)
    top = body & (relative_y > .182) & (relative_y < .535)
    if name != "NIKO":
        top &= ~skin
    jeans = body & (relative_y >= .535) & (relative_y < .95) & ~skin
    # Make shadows in the clothes deeper while leaving seams and folds bright.
    cloth_light = red*.2126 + green*.7152 + blue*.0722
    fabric_curve = .74 + .37*np.clip((cloth_light-35)/145,0,1)
    paint[top] *= fabric_curve[top,None] * np.array(TOP_BALANCE[name])
    pants_balance = (1.01,1.09,.86) if name in ("CLAUDE","FRANKLIN") else (.79,1.01,1.17)
    paint[jeans] *= fabric_curve[jeans,None] * np.array(pants_balance)
    paint = np.clip(paint,0,255)
    inner = np.asarray(Image.fromarray(body).convert("L").filter(ImageFilter.MinFilter(3))) > 127
    soft = np.asarray(Image.fromarray(np.uint8(paint)).filter(ImageFilter.GaussianBlur(.88)),
                      dtype=np.float32)
    paint[inner] += (paint[inner]-soft[inner])*.72
    left_edge = body & ~np.roll(body,1,axis=1)
    right_edge = body & ~np.roll(body,-1,axis=1)
    rim = np.where(head,.15,.28)[...,None]
    paint[left_edge] = paint[left_edge]*(1-rim[left_edge])+np.asarray(accent)*rim[left_edge]
    rim = np.where(head,.12,.22)[...,None]
    paint[right_edge] = paint[right_edge]*(1-rim[right_edge])+np.array([255,188,174])*rim[right_edge]
    return np.clip(paint,0,255)


def ascii_image(rgb, weight):
    rows,cols,height,width = weight.shape
    tiles=np.uint8(weight[...,None]*rgb.astype(np.float32,copy=False)[:,:,None,None,:])
    return Image.fromarray(tiles.transpose(0,2,1,3,4).reshape(rows*height,cols*width,3))


def detailed_background(scene, view, shade, contour, balance, index, size):
    # Fine scenery glyphs preserve steelwork and foliage behind the larger cast glyphs.
    row,_,grain,_=sample_geometry(DETAIL_GRID)
    back=grid_sample(scene,view,DETAIL_GRID)
    rgb=backdrop_colors(back,balance,index,row)
    light=rgb[...,0]*.25+rgb[...,1]*.58+rgb[...,2]*.17
    ramp=".:;+=*#%@"
    cell=(size[0]//DETAIL_GRID[0],round(size[1]/DETAIL_GRID[1]))
    chars,atlas=glyph_masks(cell)
    levels=np.clip((light/23+grain*.46).astype(np.intp),0,len(ramp)-1)
    symbols=np.array([chars.index(c) for c in ramp])[levels]
    shadow=np.asarray(shade.resize(DETAIL_GRID,Image.Resampling.BILINEAR))/255
    edge=np.asarray(contour.resize(DETAIL_GRID,Image.Resampling.BILINEAR))/255
    rgb*=(1-shadow*.32)[...,None]
    rgb*=(1-edge*.20)[...,None]
    image=ascii_image(rgb,.12+.88*atlas[symbols])
    return image if image.size == size else image.resize(size,Image.Resampling.LANCZOS)


@lru_cache(maxsize=2)
def character_atlas(cell):
    _,tiles=glyph_tiles(cell,font_size=cell[1])
    return (tiles.astype(np.float32)/255)**.72


@lru_cache(maxsize=len(GAME_LABELS)*len(PORTRAIT_SIZES))
def game_label(index, scale=1):
    text = GAME_LABELS[index]
    face = display_font(round(54*scale))
    margin = round(7*scale)
    layer = Image.new("RGBA", (math.ceil(face.getlength(text)) + 2*margin, round(72*scale)))
    ImageDraw.Draw(layer).text((margin,margin),text,font=face,anchor="lt",
                               fill="#f8ebda",stroke_width=round(3*scale),stroke_fill="#171a25")
    return layer


@lru_cache(maxsize=2)
def opening_text(scale=1):
    title = Image.new("RGBA", (round(640*scale), round(62*scale)))
    subtitle = Image.new("RGBA", (round(640*scale), round(50*scale)))
    anchor = (round(632*scale),round(4*scale))
    stroke = round(3*scale)
    ImageDraw.Draw(title).text(anchor,"GTA EVOLUTION",font=display_font(round(64*scale)),anchor="rt",
                              fill="#f8ebda",stroke_width=stroke,stroke_fill="#171a25")
    ImageDraw.Draw(subtitle).text(anchor,"CODED IN PYTHON / ASCII TEXT",font=font(round(38*scale)),anchor="rt",
                                 fill="#ffd8ac",stroke_width=stroke,stroke_fill="#171a25")
    return title,subtitle


def render(index,time,duration,*,size=SIZE):
    detailed=index in (0,5)
    scene,cast,sign=draw_scene(index,time,duration)
    moving_details(scene,index,time)
    row,col,grain,_=sample_geometry()
    cell=(size[0]//COLS,size[1]//ROWS)
    chars,atlas=glyph_masks(cell)
    view=camera(time,duration,index)
    back=grid_sample(scene,view)
    balance,accent=COLOR[index]
    rgb=backdrop_colors(back,balance,index,row)
    light=np.max(rgb,axis=2)
    ramp=".:;+=*#%@"
    levels=np.clip((light/25+grain*.82).astype(np.intp),0,len(ramp)-1)
    glyphs=np.array([chars.index(c) for c in ramp])[levels]

    sampled=[(words,grid_sample(layer,view)) for words,layer in cast]
    alpha=np.maximum.reduce([layer[...,3] for _,layer in sampled])
    silhouette=Image.fromarray(np.uint8(alpha))
    contour=silhouette.filter(ImageFilter.MaxFilter(3))
    shade=silhouette.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.4))
    if not detailed:
        rgb*=(1-np.asarray(shade,dtype=np.float32)*.53/255)[...,None]
        rgb*=(1-np.asarray(contour,dtype=np.float32)*.24/255)[...,None]
    people=np.zeros((ROWS,COLS),dtype=bool)
    for words,layer in sampled:
        body=layer[...,3]>123
        people|=body
        letters=np.array([chars.index(c) for c in words])
        glyphs[body]=letters[(col+2*row)%len(letters)][body]
        paint=character_colors(layer,body,words,accent,row)
        if index==0 and time<.79:
            # A soft scan highlights the actual name glyphs on Claude's jacket.
            band=np.exp(-((row/ROWS-(.43+time*.65))/.049)**2)
            paint=paint*(1-band[...,None]*.35)+band[...,None]*np.array([104,232,245])*.35
        rgb[body]=paint[body]
    weight=.085+.915*atlas[glyphs]
    weight[people]=.09+.91*character_atlas(cell)[glyphs[people]]
    image=ascii_image(rgb,weight)
    if detailed:
        background=detailed_background(scene,view,shade,contour,balance,index,size)
        mask=Image.fromarray(people).convert("L").resize(size,Image.Resampling.NEAREST)
        background.paste(image,mask=mask)
        image=background
    zoom,left,top=view
    scale=size[0]/SIZE[0]
    sign=sign.transform(size,Image.Transform.AFFINE,(zoom/scale,0,left*2,0,zoom/scale,top*2),
                        Image.Resampling.BICUBIC)
    image.paste(sign,mask=sign.getchannel("A"))
    label=game_label(index,scale)
    image.paste(label,tuple(round(value*scale) for value in LABEL_POSITION),label.getchannel("A"))
    if index == 5:
        midtone_curve = [round(255 * (value / 255)**.82) for value in range(256)]
        image = ImageEnhance.Color(image.point(midtone_curve * 3)).enhance(1.035)
    return image


def frame(time, durations=FINAL_DURATIONS, *, size=SIZE):
    elapsed=time%sum(durations)
    local=elapsed
    for index,duration in enumerate(durations):
        if local<duration:
            image=render(index,local,duration,size=size)
            if elapsed<OPENING_COPY_SECONDS:
                scale=size[0]/SIZE[0]
                title,subtitle=opening_text(scale)
                if index==0:
                    opacity=1-ease((local-(duration-.28))/.28)
                    mask=title.getchannel("A").point(lambda value:round(value*opacity))
                    image.paste(title,(round(360*scale),round(284*scale)),mask)
                image.paste(subtitle,(round(360*scale),round(348*scale)),subtitle.getchannel("A"))
            return image
        local-=duration


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export",type=Path)
    parser.add_argument("--fullscreen",action="store_true")
    parser.add_argument("--width",type=int,choices=PORTRAIT_SIZES,default=1080)
    parser.add_argument("--fps",type=int,choices=(30,60),default=30)
    cut=parser.add_mutually_exclusive_group()
    cut.add_argument("--short",action="store_true",help="19-second combined reel")
    cut.add_argument("--shot",choices=GAME_NAMES,help="six-second standalone game clip")
    cut.add_argument("--phone-clip",choices=GAME_NAMES,help="five-second clip from the phone sequence")
    args=parser.parse_args()
    size=PORTRAIT_SIZES[args.width]
    frame_at=partial(frame,size=size)
    seconds=sum(FINAL_DURATIONS)
    if args.short:
        frame_at=partial(frame,durations=SHORT_DURATIONS,size=size)
        seconds=sum(SHORT_DURATIONS)
    if args.phone_clip:
        seconds=PHONE_DURATIONS[0]
        offset=GAME_NAMES.index(args.phone_clip)*seconds

        def loop(time):
            return frame(offset+time%seconds,PHONE_DURATIONS,size=size)
    elif args.shot:
        frame_at=partial(render,GAME_NAMES.index(args.shot),duration=CLIP_DURATION,size=size)
        seconds=CLIP_DURATION
        def loop(time):
            return frame_at(time%CLIP_DURATION)
    else:
        loop=frame_at
    if args.export:
        gta_evolution.export(args.export,frame_at=loop,duration=seconds,size=size,fps=args.fps)
    else:
        gta_evolution.preview(args.fullscreen,frame_at=loop,title="GTA Evolution | ASCII")
