#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

# meta developer: @ZetGo

__version__ = (1, 0, 0)

import io
import math

from PIL import Image, ImageDraw

from herokutl.tl.custom import Message
from herokutl.tl.functions.help import (
    GetPeerProfileColorsRequest
)
from herokutl.tl.types import (
    EmojiStatusCollectible
)

from .. import loader, utils

def resize_image(image: Image.Image, max_size: int = 1280) -> Image.Image:
    w, h = image.size
    if max(w, h) <= max_size:
        return image
    else:
        scale = max_size / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        return image.resize((new_w, new_h), Image.LANCZOS)

# Source: https://gist.github.com/weihanglo/1e754ec47fdd683a42fdf6a272904535#file-draw_gradient_pillow-py
def get_gradient(size: tuple, color1: tuple, color2: tuple, gradient_type: str = "linear") -> Image.Image:
    def interpolate(f_co, t_co, interval):
        if interval <= 1:
            yield list(t_co)
            return

        det_co = [(t - f) / (interval - 1) for f, t in zip(f_co, t_co)]
        for i in range(interval):
            yield [round(f + det * i) for f, det in zip(f_co, det_co)]

    gradient = Image.new('RGB', size, color=(0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    if gradient_type == "linear":
        top_color, bottom_color = color1, color2

        for y, color in enumerate(interpolate(top_color, bottom_color, max(1, size[1]))):
            draw.line([(0, y), (size[0], y)], fill=tuple(color), width=1)

    elif gradient_type == "radial":
        center_color, edge_color = color1, color2

        max_radius = math.hypot(size[0], size[1]) / 2.0
        interval = max(1, int(math.ceil(max_radius)) + 1)

        colors = list(interpolate(center_color, edge_color, interval))

        cx = size[0] / 2
        cy = size[1] / 2

        for r_index, color in enumerate(colors):
            r = interval - 1 - r_index
            if r < 0:
                continue
            bbox = [
                int(round(cx - r)),
                int(round(cy - r)),
                int(round(cx + r)),
                int(round(cy + r))
            ]
            draw.ellipse(bbox, fill=tuple(color))

    return gradient

def set_gradient(im: io.BytesIO, gradient: Image.Image) -> io.BytesIO:
    img = resize_image(Image.open(im).convert('RGBA'))

    max_size = max(img.width, img.height)
    gradient = gradient.resize((max_size, max_size), Image.LANCZOS).convert('RGBA')
    left = (max_size - img.width) // 2
    top = (max_size - img.height) // 2
    gradient.paste(img, (left, top), img)
    buffer = io.BytesIO()

    gradient.save(buffer, format='PNG')

    buffer.seek(0)
    return buffer

def crop_by_bbox(img: Image.Image):
    img_w, img_h = img.size
    x, y, w, h = BBOX_TGA_TGD

    left = int(round(x * img_w))
    top = int(round(y * img_h))
    right = int(round((x + w) * img_w))
    bottom = int(round((y + h) * img_h))

    return img.crop((left, top, right, bottom))


def hex_to_rgb(value: int):
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)

def hexes_to_rgbs(value: list):
    if len(value) > 1:
        res = list()
        for i in value:
            res.append(hex_to_rgb(i))

        return tuple(res)
    else:
        res = hex_to_rgb(value[0])
        return (res, res)

SHAPES = {
 # TODO: фигуры для создания масок на авы
}

BBOX_TGA_TGD = (
    2894 / 8268,
    1260 / 8268,
    2504 / 8268,
    2504 / 8268,
)


@loader.translatable_docstring
class Gradientor(loader.Module):
    strings = {
        "name": "Gradientor",
        "_cls_doc": "A module to create your profile picture with a background from your profile",
        "gradient_creating": "<tg-emoji emoji-id=5886667040432853038>🔁</tg-emoji> Creating gradient...",
        "gradient_created": "<tg-emoji emoji-id=5818804345247894731>✅</tg-emoji> Gradient created!",
    }
    strings_ru = {
        "_cls_doc": "Модуль для создания вашей аватарки на фоне из вашего профиля",
        "gradient_creating": "<tg-emoji emoji-id=5886667040432853038>🔁</tg-emoji> Создание градиента...",
        "gradient_created": "<tg-emoji emoji-id=5818804345247894731>✅</tg-emoji> Градиент создан!",
    }

    async def client_ready(self):
        self.colors = self.get("PROFILE_COLORS", None)
        if not self.colors:
            raw_colors = (await self.client(GetPeerProfileColorsRequest(0))).colors
            self.colors = {
                str(col.color_id): hexes_to_rgbs(col.dark_colors.bg_colors) for col
                in raw_colors
            }

            self.set("PROFILE_COLORS", self.colors)

    @loader.command(
        ru_doc="[фотография/reply] - создать аватарку с градиентом из цвета профиля\n"
                "--update-cache - обновить кеш профиля, если вы только что сменили фон профиля\n"
                "--linear - использовать линейный градиент"
    )
    async def makepp(self, message: Message):
        """[photo/reply] - create a profile picture with a gradient from profile color\n
            --update-cache - update profile cache if you just changed profile background\n
            --linear - use linear gradient"""
        reply: Message = await message.get_reply_message()
        args = utils.get_args(message)

        if "--update-cache" in args:
            upd_cache = True
            args.remove("--update-cache")
        else:
            upd_cache = False
        
        if "--linear" in args:
            force_linear = True
            args.remove("--linear")
        else:
            force_linear = False

        user = None
        background_only = False

        if args:
            user = await self.client.get_entity(int(args[0]) if args[0].isdigit() else args[0])

        photo_source = (
            message
            if (not reply or not (reply.photo or reply.document and "image/" in getattr(reply.document, "mime_type", "")))
            else reply
        )
        if not (photo_source.photo or photo_source.document and "image/" in getattr(photo_source.document, "mime_type", "")):
            background_only = True

        if not user:
            if upd_cache:
                user = self.client.hikka_me = await self.client.get_me()
            elif reply:
                user = reply.sender
            else:
                user = self.client.hikka_me
        
        if not user.premium:
            color1, color2 = (28, 28, 28), (28, 28, 28)
        
        elif user.emoji_status and isinstance(user.emoji_status, EmojiStatusCollectible):
            color1, color2 = (
                user.emoji_status.edge_color, user.emoji_status.center_color
            )
            color1 = hex_to_rgb(color1)
            color2 = hex_to_rgb(color2)

        elif user.profile_color:
            color_variant = user.profile_color.color

            color1, color2 = self.colors.get(
                str(color_variant),
                ((28, 28, 28), (28, 28, 28))
            )

        else:
            color1, color2 = (28, 28, 28), (28, 28, 28)
        
        await utils.answer(message, self.strings["gradient_creating"])

        gradient = get_gradient((1280, 1280), color1, color2, "linear" if force_linear else "radial")
        gradient = crop_by_bbox(gradient)

        if not background_only:
            p_b = await photo_source.download_media(bytes)
            p_b_io = io.BytesIO(p_b)
            p_b_io.seek(0)

            result = set_gradient(p_b_io, gradient)

        else:
            result = io.BytesIO()
            gradient.save(result, format='PNG')
            result.seek(0)
        
        result.name = "grad @nullmod.png"
        
        await utils.answer(message, self.strings["gradient_created"], file=result, force_document=True)
