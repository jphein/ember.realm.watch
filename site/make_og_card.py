#!/usr/bin/env python3
"""Compose docs/assets/og-card.png — 1200x630, the social share preview.

PLACEHOLDER. lyra-artist is composing the real one from web-scale wyrm art; this
exists so the Open Graph tags are never pointing at a 404, because a broken
og:image degrades to no preview at all rather than to a plain link.

Built from the shipped device art (the LISTENING frame — full flames, wyrm alert)
so even the placeholder is honest about what the hardware draws. Palette is the
firmware's fire ramp.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
OUT = HERE / "docs/assets/og-card.png"
STATES = Path("/home/jp/Projects/ha/esphome/art/wyrm_states_shipped.png")

W, H = 1200, 630
COAL, INK, DIM = (10, 6, 4), (242, 220, 184), (165, 130, 95)
AMBER, GOLD, HOT = (224, 90, 8), (255, 168, 30), (255, 232, 180)

FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
MONO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def font(paths, size):
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), COAL)
d = ImageDraw.Draw(img)

# The listening frame is panel 1 of 5 (each 720x267). Crop to its LOWER portion —
# just the flames — because the panel's upper third is the black label strip and the
# card needs that vertical space for type, not for a screenshot of empty sky.
sheet = Image.open(STATES).convert("RGB")
panel = sheet.crop((0, 267 + 87, 720, 534))          # 720x180 of pure fire
BAND_H = int(W * panel.height / panel.width)         # 300
# Nearest-neighbour: this is pixel art, and smoothing it would misrepresent the panel.
band = panel.resize((W, BAND_H), Image.NEAREST)
img.paste(band, (0, H - BAND_H))

# Ease the band's top edge into the card so it reads as one image rather than two
# stacked ones. Alpha-composite a coal-to-transparent gradient over the first 70 rows.
FADE = 70
overlay = Image.new("RGBA", (W, FADE))
od = ImageDraw.Draw(overlay)
for i in range(FADE):
    od.line([(0, i), (W, i)], fill=COAL + (int(255 * (1 - i / FADE) ** 1.4),))
img.paste(overlay, (0, H - BAND_H), overlay)

f_title = font(FONTS, 96)
f_sub = font(FONTS, 36)
f_dim = font(FONTS, 32)
f_mono = font(MONO, 24)

d.text((64, 56), "Ember", font=f_title, fill=GOLD)
d.text((64, 176), "A voice assistant with no cloud in it.", font=f_sub, fill=INK)
d.text((64, 226), "Speech, a 35B model, and the voice — all in the house.",
       font=f_dim, fill=DIM)
d.text((64, 282), "ESP32-S3  ·  vosk  ·  Qwen3.6-35B-A3B  ·  Piper  ·  no account",
       font=f_mono, fill=AMBER)

# A rule in the fire ramp, echoing the device's own state bar.
for i in range(W - 128):
    t = i / (W - 128)
    c = tuple(int(a + (b - a) * t) for a, b in zip(AMBER, HOT))
    d.line([(64 + i, 320), (64 + i, 323)], fill=c)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, "PNG", optimize=True)
print(f"wrote {OUT}  {img.size[0]}x{img.size[1]}  {OUT.stat().st_size / 1024:.0f} KB")
