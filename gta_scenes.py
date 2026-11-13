"""The Ocean Drive and Los Santos sets and their rear-view walk cycles."""

from functools import lru_cache
from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFont


SIZE = (540, 960)


def ease(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def tint(color, amount):
    return tuple(max(0, min(255, round(value * amount))) for value in color)


@lru_cache(maxsize=12)
def font(size):
    for name in ("C:/Windows/Fonts/consolab.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                 "/System/Library/Fonts/Menlo.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


@lru_cache(maxsize=2)
def display_font(size):
    for path in ("C:/Windows/Fonts/impact.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path,size)
    return font(size)


def neon(pen, points, color, width=4):
    for spread, level in ((8, .25), (3, .58), (0, 1)):
        pen.line(points, fill=tint(color, level), width=width + spread, joint="curve")


def palm(pen, x, y, size, time, colors):
    dark, stem, leaf = colors
    at = lambda u, v: (x + u * size, y + v * size)
    pen.polygon([at(u, v) for u, v in ((-8, 0), (7, 0), (1, -100), (-21, -210),
                 (-30, -211), (-14, -99))], fill=dark)
    pen.line([at(4, -1), at(-4, -101), at(-25, -206)], fill=stem, width=max(1, round(3 * size)))
    for i in range(1, 13):
        u = i / 13
        pen.line((at(-7 - 16 * u, -207 * u), at(4 - 25 * u, -207 * u - 3)),
                 fill=stem, width=max(1, round(2 * size)))
    for i in range(10):
        angle = -3.04 + i * .32 + .04 * math.sin(time * 2.4 + i)
        length = 46 + i * 17 % 42
        vx, vy = math.cos(angle), math.sin(angle)
        path = [at(-25 + vx * length * u, -207 + vy * length * u + 28 * u ** 2)
                for u in (0, .25, .50, .75, 1)]
        pen.line(path, fill=stem, width=max(1, round(3 * size)), joint="curve")
        for j in range(1, 11):
            u = j / 11
            ox, oy = -25 + vx * length * u, -207 + vy * length * u + 28 * u ** 2
            spread = (1 - u) * 19
            for side in (-1, 1):
                end = at(ox + vx * 15 - side * vy * spread, oy + vy * 11 + side * vx * spread + 6)
                pen.line((at(ox, oy), end), fill=leaf if j % 3 else stem,
                         width=max(1, round(2 * size)))


def vice_city(time):
    image = Image.new("RGB", SIZE, (9, 7, 22))
    pen = ImageDraw.Draw(image)
    for y in range(130, 525, 5):
        haze = math.sin((y - 130) / 395 * math.pi) ** 2
        pen.rectangle((0, y, 540, y + 5), fill=(round(10 + 24 * haze), 9, round(25 + 25 * haze)))
    rng = random.Random(44)
    for i in range(65):
        x, y = rng.randrange(540), rng.randrange(130, 367)
        pen.line((x, y, x + i % 5, y), fill=(53 + i % 44, 37, 69), width=1)

    drift = round(14 * time)
    # Distant buildings on either side of the stepped Art Deco frontage.
    for i in range(7):
        left = 22 + i * 83 - drift // 2
        top = 319 + i * 41 % 80
        pen.rectangle((left, top, left + 72, 565), fill=(26, 24, 45), outline=(50, 39, 73), width=2)
        for row in range(top + 18, 548, 24):
            for col in range(left + 9, left + 67, 16):
                if (row + col) % 7:
                    pen.rectangle((col, row, col + 6, row + 9), fill=(100, 62, 92))
    x = 248 - drift
    facade = [(x - 102, 541), (x - 102, 337), (x - 68, 322), (x - 68, 301),
              (x + 3, 290), (x + 3, 262), (x + 33, 253), (x + 99, 253),
              (x + 124, 278), (x + 124, 305), (x + 210, 321), (x + 210, 539)]
    pen.polygon(facade, fill=(51, 64, 71), outline=(130, 101, 143), width=3)
    pen.polygon(((x + 132, 307), (x + 210, 320), (x + 263, 355), (x + 263, 540),
                 (x + 208, 562), (x + 208, 333)), fill=(32, 48, 72))
    for y in (345, 391, 444, 500):
        neon(pen, ((x - 101, y), (x + 209, y), (x + 261, y + 22)), (255, 80, 161), 5)
        pen.line((x - 101, y + 12, x + 209, y + 12, x + 261, y + 32),
                 fill=(82, 164, 171), width=4)
        for i in range(11):
            col = x - 94 + i * 27
            pen.rectangle((col, y + 17, col + 17, y + 36), fill=(21, 35, 53), outline=(103, 130, 146))
            pen.rectangle((col + 4, y + 19, col + 9, y + 32),
                          fill=(62 + i % 3 * 26, 100 + i % 2 * 24, 110 + i % 3 * 18))
    neon(pen, ((x + 23, 279), (x + 23, 340)), (75, 229, 217), 4)
    neon(pen, ((x + 103, 275), (x + 103, 343)), (76, 188, 229), 4)
    for i in range(8):
        col = x + 39 + i * 8
        pen.line((col, 267, col, 315), fill=(100, 105, 130), width=2)
    pen.rounded_rectangle((x - 73, 310, x + 199, 339), 5, fill=(34, 24, 47),
                          outline=(205, 62, 135), width=2)
    # Paint the marquee on a separate plate so its lettering reads at reel size.
    sign = (x + 63, 324)
    pen.rectangle((x + 13, 504, x + 99, 572), fill=(19, 42, 57))
    for i in range(4):
        pen.rectangle((x + 16 + i * 21, 510, x + 32 + i * 21, 557),
                      fill=(64, 127, 135), outline=(134, 204, 194))
    pen.line((x - 100, 573, x + 262, 557), fill=(125, 70, 134), width=4)

    pen.polygon(((0, 597), (238, 550), (540, 578), (540, 960), (0, 960)), fill=(19, 14, 32))
    pen.polygon(((0, 657), (212, 579), (521, 590), (540, 609), (162, 640), (0, 788)),
                fill=(40, 34, 60))
    pen.line((0, 787, 162, 640, 540, 609), fill=(123, 72, 114), width=3)
    pen.line((0, 902, 218, 669, 540, 624), fill=(71, 91, 127), width=2)
    for i in range(160):
        x0 = rng.randrange(540)
        y0 = 576 + (rng.randrange(390) + round(time * 36)) % 385
        d = (y0 - 568) / 390
        hue = ((141, 38, 101), (68, 133, 151), (85, 58, 124))[i % 3]
        pen.line((x0, y0, x0 + 3 + 29 * d, y0 + (i % 2)), fill=tint(hue, .36 + .60 * (1 - d)),
                 width=1 + (i % 4 == 0))
    for px, py, psize in ((83 - drift * 1.2, 620, 1.31), (505 - drift, 581, 1.0),
                          (33 - drift, 570, .75)):
        palm(pen, px, py, psize, time, ((26, 28, 41), (103, 73, 117), (51, 110, 116)))
    car = 53 + (time * 44) % 95
    pen.polygon(((car - 37, 585), (car - 20, 566), (car + 17, 563), (car + 34, 572),
                 (car + 50, 574), (car + 60, 588), (car + 54, 598), (car - 36, 599)),
                fill=(36, 46, 69), outline=(102, 114, 160))
    neon(pen, ((car + 47, 584), (car + 57, 585)), (251, 103, 107), 3)
    return image, sign


def los_santos(time):
    image = Image.new("RGB", SIZE, (16, 25, 23))
    pen = ImageDraw.Draw(image)
    for y in range(105, 501, 4):
        light = ease((y - 144) / 365)
        pen.rectangle((0, y, 540, y + 4), fill=(round(20 + 105 * light), round(31 + 82 * light),
                                                round(32 + 46 * light)))
    pen.ellipse((212, 330, 299, 417), fill=(194, 176, 107))
    for i in range(9):
        x, y = 10 + i * 64, 359 + i * 17 % 48
        pen.polygon(((x, 505), (x, y), (x + 25, y - 18), (x + 60, y + 4), (x + 60, 508)),
                    fill=(57, 68, 52), outline=(81, 89, 65))
        pen.rectangle((x + 12, y + 22, x + 31, y + 54), fill=(95, 93, 59))
    for x, y, scale in ((66, 548, 1.35), (152, 497, .87), (392, 477, .94), (500, 530, 1.34)):
        palm(pen, x, y, scale, time, ((28, 40, 29), (93, 109, 66), (56, 84, 51)))
    pen.polygon(((0, 516), (237, 468), (295, 468), (540, 584), (540, 960), (0, 960)),
                fill=(45, 42, 31))
    walls = [
        ([(0, 360), (234, 453), (234, 500), (0, 733)], (85, 76, 54), (130, 115, 75)),
        ([(291, 445), (540, 279), (540, 817), (291, 507)], (79, 63, 42), (132, 93, 58)),
    ]
    for i, (points, shade, border) in enumerate(walls):
        a, b, c, d = points
        pen.polygon(points, fill=shade, outline=border, width=3)
        for row in range(1, 12):
            v = row / 12
            edge_a = (a[0], a[1] + (d[1] - a[1]) * v)
            edge_b = (b[0], b[1] + (c[1] - b[1]) * v)
            pen.line((edge_a, edge_b), fill=tint(border, .61 + .22 * (row % 3 == 0)), width=2)
            for j in range(1, 9):
                u = ((j + (row % 2) * .48 + time * .48) % 9) / 9
                u = u ** (1.45 if i == 0 else .77)
                px = edge_a[0] + (edge_b[0] - edge_a[0]) * u
                py = edge_a[1] + (edge_b[1] - edge_a[1]) * u
                height = (d[1] - a[1]) * (1 - u) + (c[1] - b[1]) * u
                pen.line((px, py, px, py + height / 12), fill=tint(border, .67), width=1)
    pen.line(((0, 624), (234, 488)), fill=(158, 140, 93), width=4)
    pen.line(((291, 486), (540, 612)), fill=(151, 111, 73), width=4)
    for x, h in ((18, 200), (161, 323), (350, 345), (472, 248)):
        pen.line((x, h, x, 469), fill=(55, 63, 47), width=4)
        pen.line((x - 13, h + 13, x + 13, h + 13), fill=(83, 88, 55), width=3)
    pen.line(((0, 210), (165, 345), (354, 370), (540, 281)), fill=(58, 67, 54), width=2)
    pen.line(((0, 239), (162, 361), (351, 382), (540, 301)), fill=(67, 77, 58), width=2)
    rng = random.Random(301)
    for i in range(183):
        u = (rng.random() + time * .16) % 1
        y = 500 + 448 * u ** 2
        x = 264 + (rng.random() - .5) * (60 + 430 * u)
        pen.line((x, y, x + 4 + u * 20, y + 2), fill=(63 + i % 24, 63 + i % 16, 42 + i % 12),
                 width=1 + (i % 6 == 0))
    return image, None


def person(image, time, tommy, shirt_texture, head_texture):
    """Draw the planted steps, rear silhouette, fabric seams and lighting."""
    phase = time * math.tau / (1.02 if tommy else 1.27)
    walk = math.sin(phase)
    origin = 267 + (26 if tommy else 32) * math.sin((time - 1.45) * .65)
    rise = 3.2 * math.cos(phase * 2)
    head_turn = 4 * math.sin(time * 1.1)
    if not tommy:
        head_turn -= 10 * ease((time - .8) / .46) * (1 - ease((time - 1.65) / .8))
    bob = 411 + rise
    actor = Image.new("RGBA", SIZE)
    pen = ImageDraw.Draw(actor)
    skin = (193, 129, 96) if tommy else (139, 84, 57)
    lit = (230, 158, 121) if tommy else (187, 117, 79)
    dark = (115, 63, 61) if tommy else (83, 51, 42)
    rim = (134, 240, 216) if tommy else (255, 195, 123)
    ink = (27, 28, 43) if tommy else (28, 25, 25)
    pivot = lambda points: [(origin + x, bob + y) for x, y in points]

    def poly(points, fill, outline=None, width=2):
        pen.polygon(pivot(points), fill=fill)
        if outline is not None:
            pen.line(pivot(points + points[:1]), fill=outline, width=width, joint="curve")

    def line(points, color, width=2):
        pen.line(pivot(points), fill=color, width=width, joint="curve")

    ground = ImageDraw.Draw(image)
    ground.ellipse((origin - 93, 797, origin + 94, 829),
                   fill=(12, 11, 28) if tommy else (28, 31, 23))
    ground.line((origin - 72, 810, origin + 83, 812), fill=(82, 44, 83) if tommy else (71, 69, 45), width=3)

    # Back leg goes up on the swing while the other stays on the ground.
    for side in sorted((-1, 1), key=lambda side: -side * walk):
        step = side * walk
        lift = max(0, step) * 31
        hip = side * 26
        knee = side * (27 + 12 * step) + 10 * math.cos(phase)
        foot = side * (32 + 16 * step) + 12 * math.cos(phase)
        sole = 400 - lift - rise
        jeans = (44, 90, 114) if tommy else (54, 83, 111)
        jeans = tint(jeans, 1.04 - .25 * max(0, step))
        poly(((hip - 24, 203), (hip + 24, 205), (knee + 18, 294),
              (foot + 17, sole - 15), (foot - 16, sole - 12), (knee - 18, 303),
              (hip - 22, 241)), jeans, ink, 3)
        poly(((hip - 18, 223), (hip + 7, 227), (knee + 8, 297), (foot + 3, sole - 17),
              (foot - 10, sole - 22), (knee - 12, 300)), tint(jeans, 1.31))
        line(((hip + side * 16, 219), (knee + side * 14, 289),
              (foot + side * 13, sole - 18)), tint(jeans, 1.52), 3)
        for j in range(3):
            line(((knee - 14 + j * 2, 296 + j * 7), (knee + 10, 303 + j * 6)), tint(jeans, .73), 2)
        poly(((foot - 16, sole - 19), (foot + 16, sole - 19), (foot + 23, sole - 6),
              (foot + 23, sole + 2), (foot - 19, sole + 2), (foot - 22, sole - 5)),
             (111, 149, 155) if tommy else (79, 85, 76), ink, 2)
        line(((foot - 18, sole - 1), (foot + 20, sole - 1 - max(0, step) * 5)), (195, 197, 175), 3)
        line(((foot - 11, sole - 8), (foot + 13, sole - 8)), (134, 149, 139), 2)

    poly(((-51, 192), (50, 192), (52, 238), (28, 248), (-27, 247), (-52, 231)),
         (52, 80, 97), ink)
    for side in (-1, 1):
        line(((side * 13, 218), (side * 39, 216), (side * 37, 234),
              (side * 22, 239), (side * 13, 230), (side * 13, 218)), (100, 119, 121), 2)
    line(((-47, 209), (-12, 214), (11, 214), (46, 209)), (105, 79, 64), 4)

    lean = 4 * math.cos(phase)
    for side in (-1, 1):
        swing = side * math.sin(phase + .25)
        shoulder = side * 57 + lean
        elbow = side * (65 + 10 * swing) + lean
        hand = side * (72 + 16 * swing) + lean
        hy = 228 + swing * (22 if tommy else 28)
        if not tommy:
            hand -= side * 10 * ease((time - .76) / .35) * (1 - ease((time - 1.26) / .47))
        poly(((shoulder - 16, 78), (shoulder + 15, 76), (elbow + 14, 147), (hand + 11, hy - 9),
              (hand + 8, hy + 9), (hand - 3, hy + 14), (hand - 12, hy + 4), (hand - 11, hy - 10),
              (elbow - 15, 155), (shoulder - 15, 106)), skin, ink, 3)
        poly(((shoulder + side * 8, 89), (elbow + side * 10, 143), (hand + side * 9, hy - 8),
              (hand + side * 2, hy + 6), (elbow + side * 2, 149), (shoulder - side * 5, 107)),
             lit)
        line(((elbow - side * 7, 145), (hand - side * 6, hy - 13), (hand, hy - 5)), dark, 3)
        for j in range(3):
            line(((hand - 7 + j * 5, hy + 6), (hand - 4 + j * 5, hy + 10)), dark, 1)

    # Neck and head retain the cut, silhouette and head direction of the clips.
    hx = lean + head_turn
    poly(((hx - 17, 34), (hx + 15, 35), (hx + 19, 54), (hx + 33, 66),
          (hx + 15, 79), (hx - 19, 77), (hx - 31, 64), (hx - 18, 55)), skin, ink, 2)
    poly(((hx - 24, 6), (hx - 16, -7), (hx + 10, -11), (hx + 22, -3), (hx + 26, 17),
          (hx + 24, 39), (hx + 15, 53), (hx - 13, 52), (hx - 23, 41), (hx - 26, 22)),
         (62, 43, 32) if tommy else (39, 33, 28), ink, 3)
    for side in (-1, 1):
        line(((hx + side * 23, 26), (hx + side * 25, 34), (hx + side * 21, 42)), lit, 3)
    for i in range(8):
        x = hx - 18 + i * 5
        line(((x, 0 + i % 3 * 3), (x + 2, 17), (hx + (x - hx) * .65, 45 - i % 3 * 3)),
             (119, 79, 47) if tommy else (72, 58, 42), 1 + (i % 3 == 0))
    # Source hair detail follows the animated head, including the brief turn.
    head_width = round(49 - abs(head_turn) * .55)
    crop = head_texture.resize((head_width, 60), Image.Resampling.BICUBIC)
    crop.putalpha(crop.getchannel("A").point(lambda value: value * .70))
    actor.alpha_composite(crop, (round(origin + hx - head_width / 2), round(bob - 9)))
    line(((hx - 23, 11), (hx - 17, -3), (hx + 7, -8)), tint(rim, .78), 3)

    if tommy:
        outline = ((-19 + hx, 57), (21 + hx, 57), (54 + lean, 67), (66 + lean, 79),
                   (76 + lean, 122), (48, 131), (43, 154), (50, 200), (31, 213),
                   (4, 205), (-24, 216), (-52, 204), (-49, 151), (-47, 128), (-77 + lean, 121),
                   (-65 + lean, 81), (-48 + lean, 67))
        poly(outline, (61, 171, 163), ink, 3)
        if shirt_texture is not None:
            mask = Image.new("L", SIZE)
            ImageDraw.Draw(mask).polygon(pivot(outline), fill=203)
            textile = Image.new("RGB", SIZE)
            texture = shirt_texture.resize((162, 163), Image.Resampling.BICUBIC)
            textile.paste(texture, (round(origin - 81), round(bob + 55)))
            actor.paste(textile, (0, 0), mask)
        poly(((-22 + hx, 55), (20 + hx, 55), (33 + hx, 64), (5 + hx, 75), (-30 + hx, 66)),
             (92, 200, 179), (41, 102, 99))
        line(((-62 + lean, 83), (-48, 69), (-27, 67)), rim, 3)
        line(((34, 67), (57 + lean, 75), (69 + lean, 104)), (130, 208, 182), 3)
        line(((-68, 117), (-48, 125), (-45, 148), (-51, 198)), (33, 105, 101), 3)
        line(((52, 129), (49, 152), (46, 175), (51, 200)), (34, 93, 101), 3)
        line(((-46, 202), (-24, 210), (0, 203), (30, 208), (47, 199)), (105, 196, 173), 2)
        line(((-9, 78), (-2, 106), (-5, 156), (5, 197)), (106, 202, 181), 2)
    else:
        poly(((-56 + lean, 67), (-36, 59), (-28, 70), (0, 79), (26, 70), (36, 59),
              (55 + lean, 67), (54, 99), (50, 126), (42, 145), (43, 199),
              (27, 206), (-29, 206), (-46, 199), (-43, 148), (-52, 129), (-56, 94)),
             (221, 218, 201), ink, 3)
        poly(((-50, 78), (-36, 86), (-33, 113), (-23, 137), (-30, 167), (-40, 194),
              (-45, 175), (-43, 148), (-52, 129)), (153, 150, 133))
        poly(((38, 84), (51, 72), (51, 116), (42, 140), (33, 150), (29, 137)), (170, 164, 144))
        line(((-37, 67), (-31, 81), (-8, 88), (16, 86), (38, 65)), (248, 236, 209), 3)
        line(((-32, 158), (-14, 165), (15, 162), (32, 155)), (175, 168, 145), 3)
        line(((-30, 183), (-10, 193), (17, 194), (37, 184)), (251, 237, 207), 3)
        line(((-44, 201), (-18, 208), (18, 210), (41, 201)), (255, 245, 216), 2)

    image.paste(actor, (0, 0), actor)
    return actor.getchannel("A")
