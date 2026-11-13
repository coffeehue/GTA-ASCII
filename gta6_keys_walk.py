"""Jason and Lucia walk a Leonida Keys dock in colored ASCII."""
import argparse
from functools import lru_cache
import math
from pathlib import Path
import random
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from gta5_pier import Walker, sleeve_and_hand
from scenic_walk import STAGE, ease, font
from stylized_walk import (CANVAS, FPS, SIZE, arm, contact_shadows, curve_path,
                           feet_by_depth, glyph_masks, grid, leg, step_sample, walk_motion)

ROOT = Path(__file__).resolve().parent
DURATION = 6
CELL = (7, 10)
JASON_PANTS = ("#536d85","#34485f","#8b9eaf","#28364c","#414958","#bdb7ae")
LUCIA = Walker("lucia","LUCIA:CAMINOS:LEONIDA",1.06,43,.93,
               ("#ca8b72","#885861","#eeaf8f"),
               ("#39456e","#222940","#818fc1"), JASON_PANTS)


def stroke(pen, color, points, width=2):
    curve_path(pen,color,points,width=width)


def lucia_leg(pen, side, hip, phase, sway, bob, stride_gain=1):
    x, y = hip
    depth,lift,heel = step_sample(phase)
    depth *= stride_gain
    lift *= 1 + (stride_gain-1)*.62
    knee_x = x-sway*.50+side*(2+lift*.12)
    knee_y = y+100+depth*.35-lift*.62
    ankle_x = x-sway+side*(3-lift*.14)
    ankle_y = y-bob+205+.84*depth-lift-heel
    curve_path(pen,"#ce8e73",[(x-15,y-4),(x+15,y-4),
        (x+16,y+27,knee_x+10,knee_y-18,knee_x+10,knee_y),
        (knee_x+13,knee_y+25,ankle_x+7,ankle_y-23,ankle_x+7,ankle_y),
        (ankle_x+2,ankle_y+6,ankle_x-4,ankle_y+4,ankle_x-8,ankle_y),
        (ankle_x-8,ankle_y-27,knee_x-10,knee_y+30,knee_x-11,knee_y),
        (knee_x-11,knee_y-17,x-16,y+29,x-15,y-4)])
    curve_path(pen,"#986167",[(x+4,y+5),(x+15,y+1),(knee_x+10,knee_y),
        (knee_x+13,knee_y+19),(ankle_x+7,ankle_y),(ankle_x+1,ankle_y+3),
        (ankle_x+1,ankle_y-19),(knee_x+1,knee_y+15),(knee_x+2,knee_y-10)])
    stroke(pen,"#efb192",[(x-11,y+31),(knee_x-7,knee_y-10),
                          (knee_x-8,knee_y+20),(ankle_x-6,ankle_y-14)],2)
    curve_path(pen,"#e2d9cc",[(ankle_x-10,ankle_y-6),(ankle_x+8,ankle_y-5),
        (ankle_x+12,ankle_y+6,ankle_x+12,ankle_y+11,ankle_x+6,ankle_y+13),
        (ankle_x-5,ankle_y+15,ankle_x-13,ankle_y+10,ankle_x-13,ankle_y+6)])
    curve_path(pen,"#676978",[(ankle_x-10,ankle_y-4),(ankle_x+8,ankle_y-4),
        (ankle_x+12,ankle_y+7),(ankle_x+3,ankle_y+9),(ankle_x-11,ankle_y+7)])
    stroke(pen,"#bda8b1",[(ankle_x-8,ankle_y+1),(ankle_x+7,ankle_y+1)],2)


def hips(pen, lucia, sway, y):
    x=180+sway
    if lucia:
        curve_path(pen,"#353f66",[(x-39,y-24),(x+39,y-24),(x+42,y+12),
            (x+36,y+45),(x+9,y+48),(x,y+39),(x-8,y+48),(x-37,y+45),(x-43,y+13)])
        stroke(pen,"#9ba8cc",[(x-38,y+42),(x-10,y+45),(x,y+37),(x+12,y+45),(x+36,y+42)],3)
        stroke(pen,"#6379a6",[(x-38,y-9),(x,y-3),(x+37,y-10)],3)
    else:
        curve_path(pen,JASON_PANTS[0],[(x-43,y-16),(x+42,y-16),(x+43,y+17),
                                     (x+20,y+31),(x,y+20),(x-19,y+31),(x-42,y+18)])
        stroke(pen,"#8191a3",[(x-37,y+1),(x-15,y+6),(x,y+4),(x+35,y)],2)
    for side in (-1,1):
        px=x+side*20
        yy=y+10
        curve_path(pen,"#212a47" if lucia else "#415870",
                   [(px-11,yy),(px+11,yy),(px+9,yy+13),(px,yy+17),(px-10,yy+12)])
        stroke(pen,"#8799c2" if lucia else "#798fa4",
               [(px-9,yy+2),(px+9,yy+2),(px+7,yy+12),(px,yy+15),(px-8,yy+11)],1)


@lru_cache(maxsize=2)
def garment(lucia):
    img=Image.new("RGBA",CANVAS)
    pen=ImageDraw.Draw(img)
    if lucia:
        curve_path(pen,"#ca8d77",[(147,268),(202,268),(213,284),(211,302),
                                (181,308),(143,301),(141,283)])
        curve_path(pen,"#364373",[(164,170),(192,168),(206,179),(220,187),
            (230,203),(226,220),(211,226),(209,247),(214,277),
            (201,289),(172,287),(151,290),(141,278),(149,244),
            (145,224),(134,217),(133,199),(144,185)])
        curve_path(pen,"#687aa7",[(145,185),(165,175),(172,185),(159,194),
                                (151,207),(139,213),(136,201)])
        curve_path(pen,"#222947",[(194,178),(218,188),(229,205),(221,220),
                                (208,225),(208,246),(214,278),(201,286),(195,266),(194,230)])
        stroke(pen,"#9eb6e2",[(143,209),(161,211),(178,220),(203,213),(220,205)],3)
        stroke(pen,"#7489b6",[(154,216),(161,242),(157,272),(164,283)],3)
        stroke(pen,"#8199c7",[(200,218),(195,245),(201,270),(196,285)],3)
        stroke(pen,"#232c50",[(145,282),(163,286),(188,284),(210,281)],4)
        stroke(pen,"#94a6ce",[(147,282),(172,285),(199,282)],2)
        curve_path(pen,"#273353",[(159,175),(168,166),(194,168),(202,179),
                                 (189,186),(168,183)])
    else:
        curve_path(pen,"#dfd9c8",[(157,169),(204,171),(217,181),(238,189),
            (251,204),(253,225),(242,234),(225,231),(222,261),
            (228,296),(222,313),(183,318),(140,311),(138,289),
            (143,256),(137,229),(118,232),(108,224),(111,204),
            (124,186),(148,179)])
        curve_path(pen,"#b2b3b0",[(204,175),(235,187),(250,202),(252,225),(241,233),
            (225,231),(220,261),(227,298),(221,313),(199,315),(193,292),(199,263),(199,225)])
        curve_path(pen,"#f6e7ca",[(117,207),(124,188),(147,180),(158,177),
                                (164,187),(146,195),(132,214),(117,221)])
        stroke(pen,"#a1a4a4",[(146,240),(149,255),(144,276),(155,293)],3)
        stroke(pen,"#bbb6a5",[(158,285),(174,293),(199,289),(213,280)],2)
        stroke(pen,"#a9a596",[(142,305),(163,309),(191,309),(220,304)],3)
        stroke(pen,"#596272",[(111,222),(121,227),(137,226)],4)
        stroke(pen,"#596272",[(226,228),(241,229),(252,221)],4)
        curve_path(pen,"#5f646b",[(156,172),(168,165),(195,165),(205,174),
                                 (195,183),(170,183)])
    return img


def head(pen,lucia,t,x,y):
    skin="#c58872" if lucia else "#c99a80"
    stroke(pen,"#875761",[(x-15,y+58),(x-17,y+79),(x+17,y+80)],12)
    curve_path(pen,skin,[(x-18,y+54),(x+17,y+54),(x+19,y+74),
                        (x+25,y+83),(x+8,y+90),(x-23,y+85),(x-17,y+70)])
    pen.ellipse((x-28,y+35,x-19,y+52),fill=skin)
    pen.ellipse((x+19,y+36,x+28,y+53),fill=skin)
    if lucia:
        curl=8*math.sin(t*6.1)+2*math.sin(t*10.4)
        fall=3*math.cos(t*6.1)
        curve_path(pen,"#211725",[(x-11,y+6),(x-3,y-14,x+18,y-19,x+27,y-1),
             (x+41,y+16,x+36,y+40,x+40,y+51),
             (x+46+curl,y+69,x+54+curl,y+80+fall,x+51+curl,y+101+fall),
             (x+44+curl,y+110+fall,x+42+curl,y+121+fall,x+24+curl,y+126+fall),
             (x+27+curl,y+115,x+31+curl,y+106,x+25+curl,y+96),
             (x+13,y+77,x+18,y+67,x+19,y+55),(x+14,y+36),(x+3,y+24)])
        stroke(pen,"#75445b",[(x+8,y+1),(x+29,y+6,x+28,y+37,x+36,y+58),
                             (x+40+curl,y+69,x+46+curl,y+95,x+38+curl,y+112+fall)],3)
        stroke(pen,"#563347",[(x+18,y+21),(x+18,y+45),(x+30,y+72),
                             (x+34+curl,y+95),(x+28+curl,y+114+fall)],3)
        curve_path(pen,"#251b29",[(x-25,y+24),(x-27,y+11,x-11,y+3,x+3,y+3),
            (x+21,y+3,x+28,y+14,x+27,y+28),
            (x+24,y+44,x+20,y+62,x+9,y+67),(x-8,y+68),(x-21,y+58),(x-25,y+43)])
        stroke(pen,"#744754",[(x-22,y+19),(x-12,y+9),(x+9,y+9),(x+20,y+19)],3)
        stroke(pen,"#8f5a6a",[(x-14,y+25),(x,y+19),(x+20,y+19)],2)
        stroke(pen,"#b38a91",[(x+10,y+10),(x+19,y+13)],3)
        pen.ellipse((x-28,y+47,x-22,y+60),outline="#e9b47b",width=2)
    else:
        curve_path(pen,"#2a2024",[(x-25,y+29),(x-26,y+15,x-13,y+6,x+2,y+5),
            (x+19,y+5,x+29,y+17,x+26,y+31),
            (x+25,y+45,x+20,y+57,x+15,y+62),(x-13,y+63),(x-22,y+54),(x-25,y+42)])
        curve_path(pen,"#5b453f",[(x-24,y+29),(x-23,y+19),(x-15,y+12),
            (x+4,y+10),(x+16,y+12),(x+22,y+22),(x+7,y+20),(x-9,y+23),(x-20,y+32)])
        stroke(pen,"#876b5f",[(x-22,y+31),(x-20,y+47),(x-12,y+56)],2)
        for n in range(4):
            stroke(pen,"#533d37",[(x-14+n*7,y+14),(x-7+n*7,y+11)],2)


def walker(lucia,t,phase,sway,bob,*,stride_gain=1):
    art=Image.new("RGBA",CANVAS)
    pen=ImageDraw.Draw(art)
    turn=math.cos(phase)*stride_gain
    hip_y=299+bob
    for side,foot_phase in feet_by_depth(phase):
        joint=(180+sway+side*(18 if lucia else 20),hip_y)
        if lucia:
            lucia_leg(pen,side,joint,foot_phase,sway,bob,stride_gain)
        else:
            leg(pen,side,joint,foot_phase,False,.985,palette=JASON_PANTS,
                sway=sway,bob=bob,stride_gain=stride_gain)
    if lucia:
        shorts=Image.new("RGBA",CANVAS)
        hips(ImageDraw.Draw(shorts),True,sway,hip_y)
        art.alpha_composite(shorts.rotate(-1.65*turn,Image.Resampling.BICUBIC,
                                         center=(180+sway,hip_y)))
    else:
        hips(pen,False,sway,hip_y)
    for side in (-1,1):
        if lucia:
            sleeve_and_hand(pen,LUCIA,(180+side*43-sway*.46,200+bob-side*turn*1.3),side,side*turn*.67)
        else:
            arm(pen,side,(180+side*57+sway*.55,203+bob-side*turn),side*turn,False)
    head(pen,lucia,t,180+sway*.24,96+bob*.56)
    # Her pelvis and upper body rotate in opposition; his stride has a broader arm swing.
    tilt=1.28*turn if lucia else .75*turn
    top=garment(lucia).rotate(tilt,Image.Resampling.BICUBIC,center=(180,287))
    art.alpha_composite(top,(round(-sway*.38 if lucia else sway*.60),round(bob)))
    if lucia:
        # Redraw the hanging ponytail above the jacket where it overlaps the shoulder.
        hair=Image.new("RGBA",CANVAS)
        head(ImageDraw.Draw(hair),True,t,180+sway*.24,96+bob*.56)
        tail=hair.crop((200,113,254,226))
        art.alpha_composite(tail,(200,113))
    return art


@lru_cache(maxsize=1)
def distant_marina():
    image=Image.new("RGB",STAGE)
    pen=ImageDraw.Draw(image)
    stops=((0,(41,37,102)),(201,(105,69,143)),(350,(207,104,145)),(469,(255,174,121)))
    for (top,a),(bottom,b) in zip(stops,stops[1:]):
        for y in range(top,bottom+1):
            u=(y-top)/(bottom-top)
            pen.line((0,y,540,y),fill=tuple(round(x+(z-x)*u) for x,z in zip(a,b)))
    pen.ellipse((64,294,172,402),fill="#ffc57e")
    for y in (345,363,385):
        pen.line((46,y,187,y),fill="#d68099",width=3)
    for x,y,w in ((-2,248,169),(319,201,178),(356,298,204),(12,403,202)):
        pen.line((x,y,x+w,y),fill="#b77aa2",width=2)
    rng=random.Random(17)
    for x in range(-10,560,14):
        y=427+rng.randrange(-16,21)
        pen.ellipse((x,y,x+40,476),fill="#42486e")
        pen.line((x+4,y+20,x+12,468),fill="#535779",width=2)
    for y in range(469,960):
        u=(y-469)/491
        pen.line((0,y,540,y),fill=(round(70-40*u),round(98-36*u),round(127-35*u)))
    return image


def boat(pen,x,y,size,t,flip=False):
    z=math.sin(t*1.4+x*.06)*2.1

    def pt(a,b):
        return x+size*(-a if flip else a),y+size*b+z

    def shape(color, points):
        pen.polygon([pt(a,b) for a,b in points],fill=color)

    shape("#2c405a",[(-72,26),(44,25),(77,16),(54,33),(-57,36)])
    shape("#e8ceb2",[(-66,4),(42,3),(75,-6),(58,19),(39,28),(-56,27)])
    shape("#304562",[(-61,15),(38,15),(66,7),(58,19),(39,28),(-56,27)])
    shape("#c77e7e",[(-58,19),(38,19),(58,13),(55,17),(38,23),(-57,23)])
    shape("#fae5c7",[(-43,5),(-29,-19),(15,-21),(33,2)])
    shape("#2c3658",[(-25,-14),(-8,-15),(-10,-2),(-34,-1)])
    shape("#415f7c",[(-3,-15),(13,-16),(24,-3),(-4,-2)])
    stroke(pen,"#c89796",[pt(-60,6),pt(41,6),pt(69,-2)],max(2,round(size*3)))
    if size > 1:
        # A roof and rail set the foreground cabin boat apart from the skiffs.
        shape("#405878",[(-31,-24),(-24,-41),(14,-43),(23,-25)])
        stroke(pen,"#ebc4a9",[pt(-32,-42),pt(17,-45),pt(26,-42)],4)
        stroke(pen,"#bc9ba2",[pt(-24,-38),pt(-24,-23)],3)
        stroke(pen,"#a9d6d8",[pt(40,3),pt(45,-8),pt(63,-12)],3)
    for a,b,span in ((-53,34,29),(-18,39,34),(25,34,19)):
        drift=math.sin(t*2+a)*3
        stroke(pen,"#aa829c",[pt(a+drift,b),pt(a+span+drift,b)],max(2,round(size*2)))


def marina_palm(pen,x,y,size,t,mirror=False):
    sway=math.sin(t*1.55+x*.035)
    crown_x=-22+3*sway
    crown_y=-204

    def pt(a,b):
        return x+size*(-a if mirror else a),y+size*b

    pen.polygon([pt(a,b) for a,b in
        ((-9,0),(8,0),(3,-78),(crown_x+6,crown_y),
         (crown_x-6,crown_y),(-12,-78))],fill="#2d304b")
    stroke(pen,"#947787",[pt(4,-2),pt(-3,-78),pt(crown_x+2,crown_y)],max(2,round(size*3)))
    for n in range(1,10):
        u=n/10
        center=(crown_x+2)*u
        stroke(pen,"#62536f",[pt(center-5,-198*u),pt(center+5,-198*u-4)],2)

    fronds=(
        (-88,28,-47,-20),(-96,-17,-46,-41),(-70,-54,-32,-62),
        (-24,-74,-21,-54),(30,-78,13,-60),(77,-47,37,-55),
        (101,-1,51,-34),(72,34,53,-8),
    )
    for i,(dx,dy,bx,by) in enumerate(fronds):
        dy+=sway*(6+i%3)
        by+=sway*3
        spine=[]
        for j in range(10):
            u=j/9
            a=crown_x+2*(1-u)*u*bx+u*u*dx
            b=crown_y+2*(1-u)*u*by+u*u*dy
            spine.append((a,b))
        for j in range(2,9):
            a,b=spine[j]
            na,nb=spine[j+1]
            length=math.hypot(na-a,nb-b)
            ux,uy=(na-a)/length,(nb-b)/length
            spread=(6+9*math.sin(math.pi*j/9))*(1-j/12)
            for side in (-1,1):
                tip=pt(a+ux*15-uy*spread*side,b+uy*15+ux*spread*side+4)
                pen.polygon([pt(a,b),pt(a+ux*8,b+uy*8),tip],
                            fill="#35425a" if side<0 else "#26384d")
        stroke(pen,"#657083" if i%3==1 else "#3f4d64",
               [pt(a,b) for a,b in spine],max(2,round(size*3)))


def marina(t):
    art=distant_marina().copy()
    pen=ImageDraw.Draw(art)
    rng=random.Random(19)
    for n in range(156):
        y=471+(rng.random()+t*.037)%1*470
        x=rng.randrange(-40,540)
        width=rng.randrange(6,48)*(1+(y-470)/630)
        pen.line((x,y,x+width,y),fill=("#597b91","#6c7592","#826d8c","#60949f")[n%4],
                 width=1+int(n%3==0))
    for x,y,s,flip in ((403,541,.61,False),(98,613,.92,False),(439,683,1.10,True)):
        boat(pen,x,y,s,t,flip)
    # Pilings and a pastel boat shed give the boardwalk a clear destination.
    for x,y in ((216,489),(252,485),(302,480),(342,475)):
        pen.line((x,y,x,y+86),fill="#665575",width=6)
    pen.polygon([(193,414),(252,367),(352,383),(365,475),(201,495)],fill="#aa998e")
    pen.polygon([(249,367),(344,379),(378,404),(281,395),(188,434)],fill="#796983")
    pen.polygon([(201,427),(280,400),(283,488),(201,500)],fill="#c7a1a0")
    pen.polygon([(281,398),(362,408),(365,475),(283,489)],fill="#a88f94")
    for x in range(207,281,10):
        pen.line((x,429-(x-208)*.31,x,496-(x-208)*.15),fill="#92768a",width=1)
    pen.rectangle((223,442,260,491),fill="#6a617d",outline="#b88fa0",width=3)
    pen.rectangle((231,450,251,478),fill="#efb384")
    pen.rectangle((304,426,352,450),fill="#645f79",outline="#d2aeb2",width=2)
    pen.line((328,427,328,449),fill="#bf9cae",width=2)
    pen.rounded_rectangle((227,407,352,428),radius=3,fill="#665274",outline="#e9b3a0",width=1)
    for x,y,s,mirror in ((511,505,.72,True),(93,515,1.03,True),(452,502,1.20,False)):
        marina_palm(pen,x,y,s,t,mirror)
    # Project the plank spacing and pilings using distance from the moving camera.
    horizon=461
    dock_center=275
    pen.polygon([(240,495),(310,495),(475,960),(63,960)],fill="#77677f")
    pen.line((240,495,63,960),fill="#c0a193",width=5)
    pen.line((310,495,475,960),fill="#c0a193",width=5)
    for i in range(5,70):
        z=i*.84-.34*t
        y=horizon+2200/z
        if not 500<y<960:
            continue
        left=240-(y-495)*177/465
        right=310+(y-495)*165/465
        pen.line((left,y,right,y),fill="#5b506d",width=2 if y>700 else 1)
        pen.line((left,y+2,right,y+2),fill="#8f7b89",width=1)
        if i%4==0:
            height=14+38*(y-496)/464
            for x in (left,right):
                pen.line((x,y+13,x,y-height),fill="#67546e",width=6)
                pen.line((x-2,y-height+2,x+3,y-height+1),fill="#c1a092",width=2)
    for fraction in (-.31,.02,.34):
        pen.line((dock_center+fraction*66,498,dock_center+fraction*409,960),fill="#6a5b76",width=2)
    for i in range(3):
        x=(383+i*37+t*(18+i*2))%580-20
        y=283-i*11+5*math.sin(t*2+i)
        beat=5*math.sin(t*6+i)
        stroke(pen,"#5f547e",[(x-10,y+beat),(x-3,y-2),(x,y),(x+4,y-2),(x+11,y+beat)],2)
    return art


@lru_cache(maxsize=1)
def sign():
    layer=Image.new("RGBA",SIZE)
    pen=ImageDraw.Draw(layer)
    pen.text((579,835),"K E Y S  B O A T Y A R D",font=font(19),anchor="mm",fill="#ffe0b1")
    return layer


@lru_cache(maxsize=1)
def scene_grain(rows,cols):
    return np.random.default_rng(63).random((rows,cols),dtype=np.float32)


def stage(t,*,stride_gain=1,cast_spacing=0):
    setting=marina(t*(1+.52*(stride_gain-1)))
    actors=[]
    for lucia,x,ground,scale,period,offset in (
            (False,210,859,.94,1.18,.03),
            (True,329,849,.91,LUCIA.stride,.43)):
        progress=t/DURATION
        x+=cast_spacing if lucia else -cast_spacing
        scale*=1+cast_spacing*.0035
        x+=(275-x)*progress*.11
        ground-=22*progress
        scale*=1-.065*progress
        local=t*(1+.24*(stride_gain-1))+offset
        phase,sway,bob=walk_motion(local,period,3.4 if lucia else 2.3)
        contact_shadows(ImageDraw.Draw(setting),x,ground,scale,phase,"#53465e",
                        stride_gain=stride_gain)
        art=walker(lucia,local,phase,sway,bob,stride_gain=stride_gain)
        sole=517 if lucia else 520
        actor=Image.new("RGBA",STAGE)
        actor.alpha_composite(art.resize(tuple(round(d*scale) for d in CANVAS),Image.Resampling.LANCZOS),
                              (round(x-180*scale),round(ground-sole*scale)))
        actors.append((lucia,actor))
    return setting,actors


def frame(t):
    cols,rows,yy,xx,_=grid(CELL)
    chars,glyphs=glyph_masks(CELL)
    setting,layers=stage(t)
    actors=[(lucia,np.asarray(actor.resize((cols,rows),Image.Resampling.BOX))) for lucia,actor in layers]
    rgb=np.asarray(setting.resize((cols,rows),Image.Resampling.BOX),dtype=np.float32)
    rgb=255*np.power(rgb/255,.84)*.93
    ramp=".:;+=*#%@"
    levels=np.clip((np.max(rgb,axis=2)/22+scene_grain(rows,cols)*.72).astype(np.intp),0,len(ramp)-1)
    symbols=np.array([chars.index(c) for c in ramp])[levels]
    silhouette=np.maximum.reduce([sprite[...,3] for _,sprite in actors])
    shade=Image.fromarray(silhouette).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    rgb*=1-np.asarray(shade)[...,None]*(.37/255)
    actor_mask=np.zeros((rows,cols),dtype=bool)
    for lucia,sprite in actors:
        visible=sprite[...,3]>106
        actor_mask|=visible
        letters="LUCIA:CAMINOS:LEONIDA" if lucia else "JASON:DUVAL:LEONIDA"
        ids=np.array([chars.index(c) for c in letters])
        symbols[visible]=ids[(xx+2*yy)%len(ids)][visible]
        body=255*np.power(sprite[...,:3].astype(np.float32)/255,.66)+9
        warm=visible & ~np.roll(visible,1,axis=1)
        body[warm]=body[warm]*.70+np.array([255,181,153])*.30
        rgb[visible]=np.minimum(255,body[visible])
    base=np.where(actor_mask,.16,.035)[:,:,None,None]
    coverage=base+(1-base)*glyphs[symbols]
    tiles=np.uint8(coverage[...,None]*rgb[:,:,None,None,:])
    pixels=tiles.transpose(0,2,1,3,4).reshape(rows*CELL[1],cols*CELL[0],3)
    image=Image.new("RGB",SIZE,(18,13,32))
    image.paste(Image.fromarray(pixels),((SIZE[0]-pixels.shape[1])//2,0))
    lettering=sign()
    image.paste(lettering,mask=lettering.getchannel("A"))
    return image


def export(path):
    import imageio_ffmpeg

    if path.exists():
        raise FileExistsError(path)
    with TemporaryDirectory(dir=path.parent) as directory:
        temp=Path(directory)/"walk.mp4"
        writer=imageio_ffmpeg.write_frames(str(temp),SIZE,fps=FPS,codec="libx264",
            pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=1,
            output_params=["-crf","14","-preset","medium","-movflags","+faststart"])
        writer.send(None)
        try:
            for index in range(DURATION*FPS):
                writer.send(np.asarray(frame(index/FPS)))
        finally:
            writer.close()
        temp.rename(path)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export",type=Path,default=ROOT/"gta6-leonida-keys-walk-ascii.mp4")
    export(parser.parse_args().export)
