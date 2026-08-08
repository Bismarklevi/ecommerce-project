from dataclasses import dataclass
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFilter, ImageFont


@dataclass(frozen=True)
class StudioTheme:
    background_top: tuple[int, int, int]
    background_bottom: tuple[int, int, int]
    garment: tuple[int, int, int]
    accent: tuple[int, int, int]
    highlight: tuple[int, int, int]
    shadow: tuple[int, int, int]


THEMES = [
    StudioTheme((248, 243, 235), (225, 214, 199), (178, 144, 109), (112, 94, 76), (255, 248, 238), (92, 77, 62)),
    StudioTheme((240, 244, 247), (214, 223, 229), (80, 110, 142), (36, 56, 80), (246, 250, 255), (47, 61, 77)),
    StudioTheme((245, 241, 231), (221, 212, 193), (142, 141, 111), (98, 92, 73), (255, 251, 243), (76, 71, 56)),
    StudioTheme((247, 239, 237), (225, 207, 200), (171, 100, 87), (110, 59, 50), (255, 247, 246), (91, 48, 42)),
    StudioTheme((239, 240, 236), (214, 217, 209), (74, 92, 76), (44, 56, 46), (247, 251, 246), (52, 62, 53)),
]


def theme_for_name(name: str) -> StudioTheme:
    normalized = sum(ord(character) for character in name.lower())
    return THEMES[normalized % len(THEMES)]


def garment_kind_for_name(name: str) -> str:
    lower_name = name.lower()
    if any(keyword in lower_name for keyword in ("jacket", "overshirt", "blazer", "coat")):
        return "jacket"
    if any(keyword in lower_name for keyword in ("trouser", "pants", "jean", "denim")):
        return "trousers"
    if any(keyword in lower_name for keyword in ("dress", "skirt", "gown")):
        return "dress"
    return "shirt"


def _load_font(size: int) -> ImageFont.ImageFont:
    for font_name in (
        "arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _hex_like(color: tuple[int, int, int], alpha: int = 255) -> tuple[int, int, int, int]:
    return (*color, alpha)


def _gradient_canvas(size: tuple[int, int], top_color: tuple[int, int, int], bottom_color: tuple[int, int, int]) -> Image.Image:
    _, height = size
    top_layer = Image.new("RGBA", size, _hex_like(top_color))
    bottom_layer = Image.new("RGBA", size, _hex_like(bottom_color))
    mask = Image.linear_gradient("L").resize((1, height)).resize(size)
    return Image.composite(bottom_layer, top_layer, mask)


def _add_soft_glow(canvas: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int], opacity: int) -> None:
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    left = center[0] - radius
    top = center[1] - radius
    right = center[0] + radius
    bottom = center[1] + radius
    glow_draw.ellipse((left, top, right, bottom), fill=_hex_like(color, opacity))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=radius // 2))
    canvas.alpha_composite(glow)


def _draw_shadow(canvas: Image.Image) -> None:
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.ellipse((330, 1040, 870, 1215), fill=(60, 40, 28, 100))
    shadow_draw.ellipse((380, 1090, 820, 1185), fill=(75, 52, 38, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=38))
    canvas.alpha_composite(shadow)


def _draw_buttons(draw: ImageDraw.ImageDraw, x_center: int, top: int, count: int, color: tuple[int, int, int]) -> None:
    for position in range(count):
        y_position = top + position * 96
        draw.ellipse((x_center - 10, y_position - 10, x_center + 10, y_position + 10), fill=_hex_like(color, 255))


def _draw_seams(draw: ImageDraw.ImageDraw, garment_box: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    left, top, right, bottom = garment_box
    center_x = (left + right) // 2
    draw.line((center_x, top + 18, center_x, bottom - 40), fill=_hex_like(accent, 140), width=5)
    draw.line((left + 90, top + 110, left + 150, bottom - 120), fill=_hex_like(accent, 110), width=4)
    draw.line((right - 90, top + 110, right - 150, bottom - 120), fill=_hex_like(accent, 110), width=4)


def _draw_shirt_like_garment(draw: ImageDraw.ImageDraw, theme: StudioTheme, garment_type: str) -> None:
    body_box = (370, 360, 830, 1080)
    sleeve_color = _hex_like(theme.garment, 255)
    body_color = _hex_like(theme.garment, 255)
    collar_color = _hex_like(theme.accent, 255)

    draw.rounded_rectangle(body_box, radius=120, fill=body_color, outline=_hex_like(theme.shadow, 120), width=4)
    draw.polygon([(370, 420), (270, 590), (330, 1090), (470, 1090), (500, 720), (525, 450)], fill=sleeve_color)
    draw.polygon([(830, 420), (930, 590), (870, 1090), (730, 1090), (700, 720), (675, 450)], fill=sleeve_color)
    draw.polygon([(470, 360), (600, 270), (730, 360), (690, 420), (510, 420)], fill=collar_color)
    draw.polygon([(470, 360), (600, 315), (730, 360), (700, 388), (600, 342), (500, 388)], fill=_hex_like(theme.highlight, 180))

    if garment_type == "jacket":
        draw.rounded_rectangle((430, 530, 530, 615), radius=18, fill=_hex_like(theme.accent, 255))
        draw.rounded_rectangle((670, 530, 770, 615), radius=18, fill=_hex_like(theme.accent, 255))
        draw.line((480, 620, 720, 620), fill=_hex_like(theme.accent, 170), width=8)
        draw.line((600, 420, 600, 1040), fill=_hex_like(theme.highlight, 150), width=5)
    else:
        draw.line((600, 420, 600, 1050), fill=_hex_like(theme.highlight, 145), width=4)

    _draw_buttons(draw, 600, 460, 6, theme.highlight)
    _draw_seams(draw, body_box, theme.highlight)


def _draw_trousers(draw: ImageDraw.ImageDraw, theme: StudioTheme) -> None:
    waist_box = (430, 350, 770, 520)
    left_leg = [(450, 520), (575, 520), (545, 1085), (415, 1085), (390, 600)]
    right_leg = [(625, 520), (750, 520), (810, 600), (785, 1085), (655, 1085), (630, 600)]
    draw.rounded_rectangle(waist_box, radius=60, fill=_hex_like(theme.garment, 255), outline=_hex_like(theme.shadow, 100), width=4)
    draw.polygon(left_leg, fill=_hex_like(theme.garment, 255))
    draw.polygon(right_leg, fill=_hex_like(theme.garment, 255))
    draw.line((600, 520, 600, 1085), fill=_hex_like(theme.highlight, 160), width=5)
    draw.line((500, 560, 470, 1080), fill=_hex_like(theme.highlight, 120), width=4)
    draw.line((700, 560, 730, 1080), fill=_hex_like(theme.highlight, 120), width=4)
    draw.rounded_rectangle((515, 590, 565, 650), radius=10, fill=_hex_like(theme.accent, 230))
    draw.rounded_rectangle((635, 590, 685, 650), radius=10, fill=_hex_like(theme.accent, 230))


def _draw_dress(draw: ImageDraw.ImageDraw, theme: StudioTheme) -> None:
    draw.polygon([(600, 300), (470, 450), (420, 1080), (780, 1080), (730, 450)], fill=_hex_like(theme.garment, 255))
    draw.polygon([(470, 450), (365, 620), (405, 760), (495, 680), (520, 450)], fill=_hex_like(theme.garment, 255))
    draw.polygon([(730, 450), (835, 620), (795, 760), (705, 680), (680, 450)], fill=_hex_like(theme.garment, 255))
    draw.polygon([(510, 390), (600, 330), (690, 390), (670, 455), (530, 455)], fill=_hex_like(theme.accent, 255))
    draw.line((600, 455, 600, 1060), fill=_hex_like(theme.highlight, 150), width=4)
    draw.line((520, 615, 680, 615), fill=_hex_like(theme.accent, 120), width=5)


def _apply_fabric_texture(canvas: Image.Image, theme: StudioTheme, garment_type: str) -> None:
    texture = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    texture_draw = ImageDraw.Draw(texture)
    color = _hex_like(theme.highlight, 45)

    for offset in range(-220, 220, 36):
        texture_draw.line((270 + offset, 420, 910 + offset, 1030), fill=color, width=2)

    if garment_type == "jacket":
        for offset in range(-160, 200, 40):
            texture_draw.line((360 + offset, 500, 840 + offset, 980), fill=_hex_like(theme.accent, 38), width=3)
    elif garment_type == "trousers":
        for offset in range(-120, 120, 30):
            texture_draw.line((430 + offset, 540, 560 + offset, 1040), fill=_hex_like(theme.accent, 34), width=3)
            texture_draw.line((625 + offset, 540, 755 + offset, 1040), fill=_hex_like(theme.accent, 34), width=3)

    texture = texture.filter(ImageFilter.GaussianBlur(radius=1))
    canvas.alpha_composite(texture)


def render_clothing_image(product_name: str, product_description: str = "") -> ContentFile:
    theme = theme_for_name(product_name)
    garment_type = garment_kind_for_name(product_name)
    canvas = _gradient_canvas((1200, 1500), theme.background_top, theme.background_bottom)

    _add_soft_glow(canvas, (280, 280), 210, theme.highlight, 90)
    _add_soft_glow(canvas, (920, 420), 260, theme.accent, 65)
    _add_soft_glow(canvas, (650, 1040), 300, theme.shadow, 70)

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    _draw_shadow(canvas)

    hanger_color = _hex_like(theme.shadow, 190)
    overlay_draw.line((450, 210, 750, 210), fill=hanger_color, width=8)
    overlay_draw.line((600, 210, 600, 285), fill=hanger_color, width=8)
    overlay_draw.arc((540, 190, 660, 260), start=0, end=180, fill=hanger_color, width=8)

    if garment_type == "trousers":
        _draw_trousers(overlay_draw, theme)
    elif garment_type == "dress":
        _draw_dress(overlay_draw, theme)
    else:
        _draw_shirt_like_garment(overlay_draw, theme, garment_type)

    _apply_fabric_texture(overlay, theme, garment_type)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.2))
    canvas.alpha_composite(overlay)

    border_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border_layer)
    border_draw.rounded_rectangle((70, 70, 1130, 1430), radius=44, outline=_hex_like(theme.highlight, 75), width=3)
    canvas.alpha_composite(border_layer)

    title_font = _load_font(52)
    subtitle_font = _load_font(28)
    caption_font = _load_font(22)
    caption = product_description.strip() or "Studio-generated product image"

    text_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_draw.rounded_rectangle((90, 1240, 620, 1388), radius=32, fill=_hex_like(theme.highlight, 110))
    text_draw.text((130, 1268), product_name, font=title_font, fill=_hex_like(theme.shadow, 255))
    text_draw.text((130, 1330), caption[:58], font=subtitle_font, fill=_hex_like(theme.shadow, 210))
    text_draw.text((885, 1385), "KAIRA", font=caption_font, fill=_hex_like(theme.shadow, 160), anchor="ra")
    canvas.alpha_composite(text_layer)

    buffer = BytesIO()
    canvas.convert("RGB").save(buffer, format="JPEG", quality=92, optimize=True)
    filename = f"{slugify(product_name)}-studio.jpg"
    return ContentFile(buffer.getvalue(), name=filename)
