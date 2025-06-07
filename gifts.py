#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]
v = ("o", "ka", "k")
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
# -      error       - #
from herokutl.errors.rpcerrorlist import DocumentInvalidError
# -      end       - #

@loader.tds
class Gifts(loader.Module):
    """Just a module for working with gifts"""

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "gift_limit",
                20,
                "0 to show first 20 gifts",
                validator=loader.validators.Integer(),
            ),
        )
        
    async def client_ready(self):
        usrnm = getattr(self._client.heroku_me, "username", "")
        self.usernames = [
            usrnm.lower()
            if usrnm else
            "",
            str(self._client.heroku_me.id)
        ]

        self.usernames.extend(
            u.username.lower()
            for u in getattr(self._client.heroku_me, "usernames", [])
            or []
        )

        self.usernames.append("me")

    strings = {
        "name": "Gifts",
        "toomany": "<emoji document_id=5019523782004441717>❌</emoji> Too many arguments",
        "notexist": "<emoji document_id=5019523782004441717>❌</emoji> User does not exist",
        # .gifts command
        "firstline": "<emoji document_id=5875180111744995604>🎁</emoji> <b>Gifts ({}/{} shown) of {}</b>",
        "exp": "<blockquote expandable>{}</blockquote>",
        "nfts": """\n{} <a href='https://t.me/nft/{}'>{} #{}</a>
  {}
  <emoji document_id=5776219138917668486>📈</emoji> <b>Availability:</b> <code>{}</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Can transfer after</b> <code>{}</code>
  <b>More details:</b> <code>.gift {}</code>\n""",
        "p": "Pinned",
        "up": "Unpinned",
        "giftline": "\n<emoji document_id=6032644646587338669>🎁</emoji> <b>Gifts ({}):</b>\n",
        "gift": "[x{}] {} — {} <emoji document_id=5951810621887484519>⭐️</emoji>\n\n",
        "doesnthave": "<emoji document_id=5325773049201434770>😭</emoji> <b>User {} doesn't have any public gifts</b>",
        # / .gifts command
        "not_available": "<i>Not available</i>",
        "docerror": "I can't show it (Invalid document ID).\nReport this to @gitneko",
    }
    strings_ru = {
        "toomany": "Слишком много аргументов",
        "notexist": "<emoji document_id=5019523782004441717>❌</emoji> Такого пользователя не существует",
        # .gifts command
        "firstline": "<emoji document_id=5875180111744995604>🎁</emoji> <b>Подарки ({}/{} показано) у {}</b>",
        "nfts": """\n{} <a href='https://t.me/nft/{}'>{} #{}</a>
  {}
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>{}</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>{}</code>
  <b>Подробнее о подарке:</b> <code>.gift {}</code>\n""",
        "p": "Закреплено",
        "up": "Не закреплено",
        "giftline": "\n<emoji document_id=6032644646587338669>🎁</emoji> <b>Подарки ({}):</b>\n",
        "doesnthave": "<emoji document_id=5325773049201434770>😭</emoji> <b>Пользователь {} не имеет публичных подарков</b>",
        # / .gifts command
        "not_available": "<i>Не доступно</i>"
        #"docerror": "nahhhhh I can't show it",
    }

    @loader.command(ru_doc="""[юзернейм/ответ/'me'] посмотреть подарки пользователя
    Команда имеет несколько флагов для фильтрации вывода:
        -n(ft) — исключить NFT
        -g(ifts) — исключить обычные подарки(розы, мишки и т.п.)
        -l(imited) — исключить редкие подарки""")
    async def gifts(self, message):
        """[username/reply/'me'] view user's gifts
        Module have some flags to filter output:
        -n(ft) — excludes nft gifts
        -g(ifts) — excludes regular gifts (not rare)
        -l(imited) — excludes limited(rare) gifts"""
        params = {} # < - excluding args
        args = utils.get_args_raw(message)
        if "-nft" in args or "-n" in args:
            args = args.replace("-nft", "").replace("-n", "")
            params["exclude_unique"] = True

        if "-gifts" in args or "-g" in args:
            args = args.replace("-gifts", "").replace("-g", "")
            params["exclude_unlimited"] = True

        if "-limited" in args or "-l" in args:
            args = args.replace("-limited", "").replace("-l", "")
            params["exclude_limited"] = True
            
        args = args.strip().split()
        if len(args) > 1:
            await utils.answer(message, self.strings["toomany"])
            return
        if len(args):
            id = args[0]
            try:
                id = int(id)
            except: pass    
        else:
            if message.is_reply:
                reply = await message.get_reply_message()
                id = reply.sender.id
            else:
                id = "me"
        user_gifts = await self._get_gifts(id, params)
        if not user_gifts:
            await utils.answer(message, self.strings["notexist"])
            return
        name = (await self.client.get_entity(id)).first_name
        if user_gifts[0]["nfts"] or user_gifts[0]["gifts"]:
            text = self.strings["firstline"].format(user_gifts[2], user_gifts[1], name)
            if user_gifts[0]["nfts"]:
                text += "\n<emoji document_id=5807868868886009920>👑</emoji> <b>NFTs ({}):</b>\n".format(user_gifts[3][0])
                nfts = ""
                for nft in user_gifts[0]["nfts"]:
                    nfts += self.strings["nfts"].format(nft["emoji"], nft["slug"], nft["name"],
                                                        nft["num"], nft["pinned_to_top"],
                                                        nft["availability_total"], nft["can_transfer_at"], nft["slug"])
                text += self.strings["exp"].format(nfts)
            if user_gifts[0]["gifts"]:
                text += self.strings["giftline"].format(user_gifts[3][1])
                gifts = ""
                for gift in user_gifts[0]["gifts"]:
                    gifts += self.strings["gift"].format(gift["count"], gift["emoji"], gift["sum"])
                text += self.strings["exp"].format(gifts)
            try:
                await utils.answer(message, text)
            except DocumentInvalidError:
                await utils.answer(message, self.strings["docerror"])
        else:
            await utils.answer(message, self.strings["doesnthave"].format(name))

    async def _get_gifts(self, username, parameters):
        gifts = [{
            "nfts": [],
            "gifts": [],
        }]
        zzz = 0
        nft_count = 0
        gifts_count = 0
        try:
            gifts_info = await self.client(GetSavedStarGiftsRequest(peer=username, offset='', limit=int(self.config["gift_limit"]), **parameters))
            gifts.append(gifts_info.count)
        except:
            raise
        shown = len(gifts_info.gifts)
        for gift in gifts_info.gifts:
            if isinstance(gift, SavedStarGift):
                if isinstance(gift.gift, StarGiftUnique):
                    nft_count += 1
                    gifts[0]["nfts"].append({
                        "emoji": "<emoji document_id={}>{}</emoji>".format(gift.gift.attributes[0].document.id, gift.gift.attributes[0].document.attributes[1].alt), 
                        "name": gift.gift.title,
                        "slug": gift.gift.slug,
                        "num": gift.gift.num,
                        "availability_total": gift.gift.availability_total,
                        "pinned_to_top": f"<emoji document_id=5796440171364749940>📌</emoji> <b>{self.strings['p']}</b>" if gift.pinned_to_top else f"<emoji document_id=5794314463200940940>📌</emoji> <b>{self.strings['up']}</b>",
                        "can_transfer_at": (
                            time.strftime("%H:%M %d.%m.%Y", time.gmtime(gift.can_transfer_at))
                            if username in self.usernames else
                            self.strings["not_available"])
                    })
                elif isinstance(gift.gift, StarGift):
                    gifts_count += 1
                    st_id = str(gift.gift.sticker.id).replace("5231003994519794860", "5253982443215547954").replace("5465502401358226185", "5298801741209299033") # < - jst dumpfix to avoid DocumentInvalidError
                    zzz = False
                    for gft in gifts[0]["gifts"]:
                        if st_id in gft["emoji"]:
                            gft["count"] += 1
                            gft["sum"] += gift.gift.stars
                            zzz = True
                            break
                    if zzz: continue
                    gifts[0]["gifts"].append({
                        "emoji": "<emoji document_id={}>{}</emoji>".format(st_id, gift.gift.sticker.attributes[1].alt),
                        "stars": f"<code>{gift.gift.stars}</code>" + " <emoji document_id=5951810621887484519>⭐️</emoji>",
                        "sum": gift.gift.stars,
                        "count": 1,
                    })
        gifts.append(shown)
        gifts.append([nft_count, gifts_count])
        return gifts
        
__version__ = v
