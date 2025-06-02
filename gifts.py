#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]

# meta developer: @nullmod
# scope: heroku_min 1.7.0
# scope: hikka_min 1.7.0

# -      main      - #
from .. import loader, utils
# -      func      - #
import time
from herokutl.tl.functions.payments import GetSavedStarGiftsRequest
# -      types     - #
from herokutl.tl.types import SavedStarGift, StarGift, StarGiftUnique, PeerUser
# -      end       - #

@loader.tds
class Gifts(loader.Module):
    """Just a module for working with gifts"""

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "gift_limit",
                20,
                "0 to show all gifts",
                validator=loader.validators.Integer(),
            ),
        )

    strings = {
        "name": "Gifts",
        "toomany": "<emoji document_id=5019523782004441717>❌</emoji> Too many arguments",
        "notexist": "<emoji document_id=5019523782004441717>❌</emoji> User does not exist",
        "firstline": "<emoji document_id=5875180111744995604>🎁</emoji> <b>Gifts({}) of {}</b>",
        "exp": "<blockquote expandable>{}</blockquote>",
        "nfts": """\n{} <a href='https://t.me/nft/{}'>{} #{}</a>
  {}
  <emoji document_id=5776219138917668486>📈</emoji> <b>Availability: </b><code>{}</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Can transfer after</b> <code>{}</code>\n""",
        "p": "Pinned",
        "up": "Unpinned",
        "giftline": "\n<emoji document_id=6032644646587338669>🎁</emoji> <b>Gifts:</b>\n",
        "gift": "{} — {}\n\n",
        "doesnthave": "<emoji document_id=5325773049201434770>😭</emoji><b> User {} doesnt have any public gifts</b>",
    }
    strings_ru = {
        "toomany": "Слишком много аргументов",
        "notexist": "<emoji document_id=5019523782004441717>❌</emoji> Такого пользователя не существует",
        "firstline": "<emoji document_id=5875180111744995604>🎁</emoji> <b>Подарки({}) у {}</b>",
        "nfts": """\n{} <a href='https://t.me/nft/{}'>{} #{}</a>
  {}
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков: </b><code>{}</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>{}</code>\n""",
        "p": "Закреплено",
        "up": "Не закреплено",
        "giftline": "\n<emoji document_id=6032644646587338669>🎁</emoji> <b>Подарки:</b>\n",
        "doesnthave": "<emoji document_id=5325773049201434770>😭</emoji><b> Пользователь {} не имеет публичных подарков</b>",
    }

    @loader.command(ru_doc="[юзернейм/ответ/'me'] посмотреть подарки пользователя")
    async def gifts(self, message):
        """[username/reply/'me'] view user's gifts"""
        args = utils.get_args_raw(message).split()
        if len(args) > 1:
            await utils.answer(message, self.strings["toomany"])
            return
        if len(args):
            id = args[0]
        else:
            if message.is_reply:
                reply = await message.get_reply_message()
                id = reply.sender.id
            else:
                id = "me"
        user_gifts = await self._get_gifts(id)
        if not user_gifts:
            await utils.answer(message, self.strings["notexist"])
            return
        name = (await self.client.get_entity(id)).first_name
        if user_gifts[0]["nfts"] or user_gifts[0]["gifts"]:
            text = self.strings["firstline"].format(user_gifts[1], name)
            if user_gifts[0]["nfts"]:
                text += "\n<emoji document_id=5807868868886009920>👑</emoji> <b>NFTs</b>\n"
                nfts = ""
                for nft in user_gifts[0]["nfts"]:
                    nfts += self.strings["nfts"].format(nft["emoji"], nft["slug"], nft["name"],
                                                        nft["num"], nft["pinned_to_top"],
                                                        nft["availability_total"], nft["can_transfer_at"])
                text += self.strings["exp"].format(nfts)
            if user_gifts[0]["gifts"]:
                text += self.strings["giftline"]
                gifts = ""
                for gift in user_gifts[0]["gifts"]:
                    gifts += self.strings["gift"].format(gift["emoji"], gift["stars"])
                text += self.strings["exp"].format(gifts)
            await utils.answer(message, text)
        else:
            await utils.answer(message, self.strings["doesnthave"].format(name))

    async def _get_gifts(self, username):
        gifts = [{
            "nfts": [],
            "gifts": [],
        }]
        try:
            gifts_info = await self.client(GetSavedStarGiftsRequest(peer=username, offset='', limit=int(self.config["gift_limit"])))
            gifts.append(gifts_info.count)
        except:
            return None
        for gift in gifts_info.gifts:
            if isinstance(gift, SavedStarGift):
                if isinstance(gift.gift, StarGiftUnique):
                    gifts[0]["nfts"].append({
                        "emoji": "<emoji document_id={}>{}</emoji>".format(gift.gift.attributes[0].document.id, gift.gift.attributes[0].document.attributes[1].alt),
                        "name": gift.gift.title,
                        "slug": gift.gift.slug,
                        "num": gift.gift.num,
                        "availability_total": gift.gift.availability_total,
                        "pinned_to_top": f"<emoji document_id=5796440171364749940>📌</emoji> <b>{self.strings['p']}</b>" if gift.pinned_to_top else f"<emoji document_id=5794314463200940940>📌</emoji> <b>{self.strings['up']}</b>",
                        "can_transfer_at": time.strftime("%H:%M %d.%m.%Y", time.gmtime(gift.can_transfer_at))
                    })
                elif isinstance(gift.gift, StarGift):
                    gifts[0]["gifts"].append({
                        "emoji": "<emoji document_id={}>{}</emoji>".format(gift.gift.sticker.id, gift.gift.sticker.attributes[1].alt),
                        "stars": f"<code>{gift.gift.stars}</code>" + " <emoji document_id=5951810621887484519>⭐️</emoji>"
                    })
        return gifts