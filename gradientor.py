#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

# meta developer: @ZetGo

__version__ = (0, 0, 1)

import io
import math

from PIL import Image, ImageDraw

from herokutl.tl.custom import Message
from herokutl.tl.types import EmojiStatusCollectible

from .. import loader, utils

# Source: https://gist.github.com/weihanglo/1e754ec47fdd683a42fdf6a272904535#file-draw_gradient_pillow-py
def get_linear_gradient(size: tuple, top_color: tuple, bottom_color: tuple) -> Image.Image:
    def interpolate(f_co, t_co, interval):
        if interval <= 1:
            yield list(t_co)
            return

        det_co = [(t - f) / (interval - 1) for f, t in zip(f_co, t_co)]
        for i in range(interval):
            yield [round(f + det * i) for f, det in zip(f_co, det_co)]

    gradient = Image.new('RGB', size, color=(0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    
    for y, color in enumerate(interpolate(top_color, bottom_color, max(1, size[1]))):
        draw.line([(0, y), (size[0], y)], fill=tuple(color), width=1)

    return gradient

def get_radial_gradient(size: tuple, center_color: tuple, edge_color: tuple) -> Image.Image:
    def interpolate(f_co, t_co, interval):
        if interval <= 1:
            yield list(t_co)
            return

        det_co = [(t - f) / (interval - 1) for f, t in zip(f_co, t_co)]
        for i in range(interval):
            yield [round(f + det * i) for f, det in zip(f_co, det_co)]

    gradient = Image.new('RGB', size, color=(0, 0, 0))
    draw = ImageDraw.Draw(gradient)

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

def get_gradient(size: tuple, color1: tuple, color2: tuple, gradient_type: str = "linear") -> Image.Image:
    if gradient_type == "linear":
        return get_linear_gradient(size, color1, color2)
    elif gradient_type == "radial":
        return get_radial_gradient(size, color1, color2)

def set_gradient(im: io.BytesIO, gradient: Image.Image) -> io.BytesIO:
    im: Image.Image = Image.open(im)

    im_composite = Image.alpha_composite(im.convert('RGBA'), gradient.convert('RGBA'))
    buffer = io.BytesIO()

    im_composite.save(buffer, format='PNG')

    buffer.seek(0)
    return buffer

PROFILE_COLORS = {
  0:  ((156, 71, 0), (156, 71, 0)),
  1:  ((148, 120, 252), (148, 120, 252)),
  2:  ((113, 96, 73), (113, 96, 73)),
  3:  ((51, 101, 123), (51, 101, 123)),
  4:  ((56, 89, 39), (56, 89, 39)),
  5:  ((71, 113, 148), (71, 113, 148)),
  6:  ((148, 127, 43), (148, 127, 43)),
  7:  ((67, 6, 97), (67, 6, 97)),
  8:  ((153, 16, 11), (171, 47, 94)),
  9:  ((143, 92, 63), (160, 160, 50)),
  10: ((99, 70, 129), (146, 112, 82)),
  11: ((41, 54, 59), (95, 95, 100)),
  12: ((48, 41, 84), (62, 67, 90)),
  13: ((56, 71, 60), (69, 114, 33)),
  14: ((136, 119, 0), (165, 165, 57)),
  15: ((83, 96, 110), (56, 70, 84)),
}

shapes = {

}

def set_shape(im: io.BytesIO, shape: str) -> io.BytesIO:

    return im


@loader.translatable_docstring
class Gradientor(loader.Module):
    strings = {
        "name": "Gradientor",
        "_cls_doc": "A module to create your profile picture with a background from your profile (primarily - the background from NFT gift)",
        "_cmd_doc_makepp": "[photo/reply] - create a profile picture with a gradient from profile color\n"
                            "--update-cache - update profile cache if you just changed profile background",
        "gradient_creating": "<tg-emoji emoji-id=5886667040432853038>🔁</tg-emoji> Creating gradient...",
        "gradient_created": "<tg-emoji emoji-id=5818804345247894731>✅</tg-emoji> Gradient created!",
    }
    strings_ru = {
        "_cls_doc": "Модуль для создания вашей аватарки на фоне из вашего профиля (в первую очередь - фон от NFT-подарка)",
        "_cmd_doc_makepp": "[фотография/reply] - создать аватарку с градиентом из цвета профиля\n"
                            "--update-cache - обновить кеш профиля, если вы только что сменили фон профиля",
        "gradient_creating": "<tg-emoji emoji-id=5886667040432853038>🔁</tg-emoji> Создание градиента...",
        "gradient_created": "<tg-emoji emoji-id=5818804345247894731>✅</tg-emoji> Градиент создан!",
    }

    async def makepp(self, message: Message):
        reply: Message = await message.get_reply_message()
        args = utils.get_args(message)

        if "--update-cache" in args:
            upd_cache = True
            args.remove("--update-cache")
        else:
            upd_cache = False

        photo_source = (message if not reply or not reply.photo else reply)
        if not photo_source.photo:
            background_only = True

        user = self.client.hikka_me = (
            (
                await self.client.get_me()
                if not reply
                else await self.client.get_entity(reply.from_id)
            ) if not upd_cache else self.client.hikka_me
        )

        emoji = False
        
        if not user.premium:
            color1, color2 = (28, 28, 28), (28, 28, 28)
        
        elif user.status and isinstance(user.status, EmojiStatusCollectible):
            color1, color2 = (
                user.status.edge_color, user.status.center_color
            )
            color1 = ((color1 >> 16) & 255, (color1 >> 8) & 255, color1 & 255)
            color2 = ((color2 >> 16) & 255, (color2 >> 8) & 255, color2 & 255)

            emoji = True

        elif user.profile_color:
            color_variant = user.profile_color.color

            color1, color2 = PROFILE_COLORS.get(
                color_variant,
                ((28, 28, 28), (28, 28, 28))
            )
        
        await utils.answer(message, self.strings["gradient_creating"])

        gradient = get_gradient((512, 512), color1, color2, "radial" if emoji else "linear")

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
