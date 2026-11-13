# GTA Evolution in ASCII

A Python renderer that draws six GTA-inspired scenes from GTA III through GTA VI using colored ASCII glyphs. The main cut runs for 31 seconds.

## Run it locally

Install Python 3.10 or newer. Open a terminal in the folder containing this README.

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe gta_evolution_vibrant.py
```

**macOS and Linux**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python gta_evolution_vibrant.py
```

The preview uses Tkinter. If your Python installation omits it, install the Tkinter package for your Python version or use the export command below. Press Esc to close the preview. Add `--fullscreen` to launch it fullscreen.

## Export an MP4

With the virtual environment activated, run:

```sh
python gta_evolution_vibrant.py --width 1440 --fps 60 --export gta-evolution.mp4
```

Use `--phone-clip gta3` to preview or export an individual five-second scene. The other scene names are `vice-city`, `san-andreas`, `gta4`, `gta5`, and `gta6`. Use `--shot gta6` for the six-second GTA VI ending.

The three San Andreas textures in `assets/` are cropped from a gameplay reference. Keep this directory alongside the Python files. The animation is an unofficial fan project inspired by the Grand Theft Auto series.
