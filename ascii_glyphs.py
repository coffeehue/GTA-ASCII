"""Fonts and character masks for the portrait renderer."""
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SIZE = (1080, 1920)


@lru_cache(maxsize=8)
def atlas(cell, font_size=None):
    w,h=cell
    candidates=['C:/Windows/Fonts/consolab.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf']
    path=next((p for p in candidates if Path(p).exists()),None)
    size = h - 1 if font_size is None else font_size
    font=ImageFont.truetype(path,size) if path else ImageFont.load_default(size=size)
    chars=' .,:;+=*#%@ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/|'
    tiles=[]
    for char in chars:
        tile=Image.new('L',cell);d=ImageDraw.Draw(tile);l,t,r,b=d.textbbox((0,0),char,font=font)
        d.text(((w-r-l)/2,(h-b-t)/2),char,font=font,fill=255);tiles.append(np.asarray(tile))
    return chars,np.stack(tiles)
