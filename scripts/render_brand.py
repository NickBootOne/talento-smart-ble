from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SCALE = 3
SIZE = 512
image = Image.new("RGBA", (SIZE * SCALE, SIZE * SCALE))
draw = ImageDraw.Draw(image)
navy = "#102A43"
teal = "#27D3C2"
white = "#F5FAFF"


def box(bounds):
    return tuple(value * SCALE for value in bounds)


def rounded(bounds, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box(bounds), radius=radius * SCALE, fill=fill, outline=outline, width=width * SCALE)


def line(points, fill, width):
    points = [(horizontal * SCALE, vertical * SCALE) for horizontal, vertical in points]
    draw.line(points, fill=fill, width=width * SCALE, joint="curve")
    radius = width * SCALE / 2
    for horizontal, vertical in points:
        draw.ellipse((horizontal - radius, vertical - radius, horizontal + radius, vertical + radius), fill=fill)


rounded((0, 0, 512, 512), 112, navy)
rounded((83, 43, 365, 466), 34, white)
rounded((133, 25, 315, 68), 13, "#C5D4E0")
rounded((111, 108, 337, 310), 23, navy)
draw.ellipse(box((154, 138, 294, 278)), outline=teal, width=11 * SCALE)
line([(224, 162), (224, 208), (258, 228)], white, 12)
rounded((115, 341, 177, 372), 14, "#D9E4EC")
rounded((194, 341, 256, 372), 14, "#D9E4EC")
rounded((115, 401, 217, 425), 12, teal)
draw.ellipse(box((264, 259, 494, 489)), fill=navy, outline=teal, width=12 * SCALE)
line([(336, 328), (419, 401), (376, 444), (376, 299), (419, 341), (336, 414)], white, 12)

for folder in [ROOT / "brand", ROOT / "custom_components/talento_smart_ble/brand"]:
    folder.mkdir(parents=True, exist_ok=True)
    for size, filename in [(256, "icon.png"), (512, "icon@2x.png")]:
        image.resize((size, size), Image.Resampling.LANCZOS).save(folder / filename, optimize=True)
print("Brand PNGs rendered at 256 and 512 pixels.")
