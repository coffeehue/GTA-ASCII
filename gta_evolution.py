"""The GTA III, Vice City, San Andreas, IV, and V ASCII walk reel."""
import argparse
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

import gta5_pier
import liberty_city_walk
import scenic_walk
from stylized_walk import FPS, SIZE

SHOTS = (
    (liberty_city_walk.DURATION, partial(liberty_city_walk.frame, "gta3")),
    (scenic_walk.SHOT, partial(scenic_walk.frame, "tommy", fade=False)),
    (scenic_walk.SHOT, partial(scenic_walk.frame, "cj", fade=False)),
    (liberty_city_walk.DURATION, partial(liberty_city_walk.frame, "gta4")),
    (gta5_pier.DURATION, gta5_pier.frame),
)
DURATION = sum(seconds for seconds, _ in SHOTS)


def frame(time):
    local_time = time % DURATION
    for seconds, draw in SHOTS:
        if local_time < seconds:
            return draw(local_time)
        local_time -= seconds


def export(path, *, frame_at=frame, duration=DURATION, size=SIZE, fps=FPS):
    import imageio_ffmpeg

    if path.exists():
        raise FileExistsError(path)
    with TemporaryDirectory(dir=path.parent) as directory:
        temporary = Path(directory) / "reel.mp4"
        writer = imageio_ffmpeg.write_frames(
            str(temporary), size, fps=fps, codec="libx264",
            pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=1,
            output_params=["-crf", "15", "-preset", "medium", "-movflags", "+faststart"],
        )
        writer.send(None)
        try:
            for index in range(duration * fps):
                writer.send(np.asarray(frame_at(index / fps)))
                if index % (fps * 5) == 0:
                    print(f"{index // fps}/{duration} seconds rendered", flush=True)
        finally:
            writer.close()
        temporary.rename(path)


def preview(fullscreen, *, frame_at=frame, title="GTA ASCII | III to V"):
    import tkinter as tk
    from time import perf_counter

    from PIL import Image, ImageTk

    window = tk.Tk()
    window.title(title)
    window.configure(bg="black")
    window.attributes("-fullscreen", fullscreen)
    height = min(window.winfo_screenheight() - (0 if fullscreen else 95),
                 round(window.winfo_screenwidth() * 16 / 9))
    display_size = (round(height * 9 / 16), height)
    label = tk.Label(window, bg="black", bd=0)
    label.pack(expand=True)
    window.bind("<Escape>", lambda _: window.destroy())
    start = perf_counter()

    def tick():
        now = perf_counter()
        picture = frame_at(now - start).resize(display_size, Image.Resampling.LANCZOS)
        label.image = ImageTk.PhotoImage(picture)
        label.configure(image=label.image)
        window.after(max(1, 33 - round((perf_counter() - now) * 1000)), tick)

    tick()
    window.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--export", type=Path)
    args = parser.parse_args()
    if args.export:
        export(args.export)
    else:
        preview(args.fullscreen)
