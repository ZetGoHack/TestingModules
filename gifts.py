#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]
v = ("oooo", "kaaa", "kkkk")
# meta developer: @nullmod & @codermasochist
# scope: heroku_min 1.7.2
# scope: hikka_min 1.7.2

from .. import loader, utils
# -      func      - #
import asyncio
import time
from herokutl.tl.functions.payments import GetSavedStarGiftsRequest, GetUniqueStarGiftRequest
# -      types     - #
from herokutl.tl.types import (
    Channel, User, SavedStarGift, StarGift,
    StarGiftUnique, StarGiftAttributeModel,
    StarGiftAttributePattern, StarGiftAttributeBackdrop
)
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
                "0 to show first 100 gifts",
                validator=loader.validators.Integer(minimum=0),
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
        "noargs": "<emoji document_id=5019523782004441717>❌</emoji> No arguments provided",
        "toomany": "<emoji document_id=5019523782004441717>❌</emoji> Too many arguments",
        "unotexist": "<emoji document_id=5019523782004441717>❌</emoji> User does not exist",
        "not_user_or_channel": "<emoji document_id=5019523782004441717>❌</emoji> This is not a user or channel",
        "gifterr": "<emoji document_id=5019523782004441717>❌</emoji> Gift slug is invalid",
        # .gifts command
        "loading": "<emoji document_id=6030657343744644592>🔁</emoji> Fetching gifts...",
        "firstline": "<emoji document_id=5875180111744995604>🎁</emoji> <b>Gifts ({}/{} shown) of {}</b>",
        "exp": "<blockquote expandable>{}</blockquote>",
        "nfts": """\n{} <a href='https://t.me/nft/{}'>{} #{}</a>
  {}
  <emoji document_id=5776219138917668486>📈</emoji> <b>Availability:</b> <code>{}</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Can transfer after</b> <code>{}</code>\n""",
        "p": "Pinned",
        "up": "Unpinned",
        "giftline": "\n<emoji document_id=6032644646587338669>🎁</emoji> <b>Gifts ({}) - {} <emoji document_id=5951810621887484519>⭐️</emoji>:</b>\n",
        "gift": "[x{}] {} — {} <emoji document_id=5951810621887484519>⭐️</emoji>\n\n",
        "doesnthave": "<emoji document_id=5325773049201434770>😭</emoji> <b>{} doesn't have any public gifts</b>",
        # / .gifts command
        "not_available": "<i>Not available</i>",
        "nft": "<a href='t.me/nft/{}'>\u200f</a>",
        "docerror": "I can't show it (Invalid document ID).\nReport this message to @gitneko.\n{}",
    }
    strings_ru = {
        "toomany": "<emoji document_id=5019523782004441717>❌</emoji> Слишком много аргументов",
        "noargs": "<emoji document_id=5019523782004441717>❌</emoji> Вы не указали аргументы",
        "unotexist": "<emoji document_id=5019523782004441717>❌</emoji> Такого пользователя не существует",
        "not_user_or_channel": "<emoji document_id=5019523782004441717>❌</emoji> Это не пользователь и не канал",
        "gifterr": "<emoji document_id=5019523782004441717>❌</emoji> Некорректный id подарка",
        # .gifts command
        "loading": "<emoji document_id=6030657343744644592>🔁</emoji> Получаю подарки...",
        "firstline": "<emoji document_id=5875180111744995604>🎁</emoji> <b>Подарки ({}/{} показано) у {}</b>",
        "nfts": """\n{} <a href='https://t.me/nft/{}'>{} #{}</a>
  {}
  <emoji document_id=5776219138917668486>📈</emoji> <b>Всего подарков:</b> <code>{}</code>
  <emoji document_id=5776213190387961618>🕓</emoji> <b>Возможно передать после</b> <code>{}</code>\n""", 
        "p": "Закреплено",
        "up": "Не закреплено",
        "giftline": "\n<emoji document_id=6032644646587338669>🎁</emoji> <b>Подарки ({}) - {} <emoji document_id=5951810621887484519>⭐️</emoji>:</b>\n",
        "doesnthave": "<emoji document_id=5325773049201434770>😭</emoji> <b>{} не имеет публичных подарков</b>",
        # / .gifts command
        "not_available": "<i>Не доступно</i>",
        "nft": "<a href='t.me/nft/{}'>\u200f</a>",
    }

    @loader.command(ru_doc="""[юзернейм/ответ/'me'] посмотреть подарки пользователя
    Команда имеет несколько флагов для фильтрации вывода:
        -n(ft) — исключить NFT
        -g(ifts) — исключить обычные подарки(розы, мишки и т.п.)
        -l(imited) — исключить редкие подарки
        -u(pgradable) — показать только улучшаемые подарки
        -s(aved) — показать только не скрытые подарки""")
    async def gifts(self, message):
        """[username/reply/'me'] view user's gifts
        Module have some flags to filter output:
        -n(ft) — excludes nft gifts
        -g(ifts) — excludes regular gifts (not rare)
        -l(imited) — excludes limited(rare) gifts
        -u(pgradable) — shows only upgradable gifts
        -s(aved) — shows only not hidden gifts"""
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
            params["exclude_unupgradable"] = True

        if "-upgradable" in args or "-u" in args:
            args = args.replace("-upgradable", "").replace("-u", "")
            params["exclude_upgradable"] = True

        if "-saved" in args or "-s" in args:
            args = args.replace("-saved", "").replace("-s", "")
            params["exclude_unsaved"] = True
            
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

        await utils.answer(message, self.strings["loading"])

        user_gifts = await self._get_gifts(id, params)
        if not user_gifts:
            await utils.answer(message, self.strings["unotexist"])
            return
        entity = await self.client.get_entity(id)
        if isinstance(entity, (Channel, User)):
            name = entity.first_name if hasattr(entity, "first_name") else entity.title
        else:
            await utils.answer(message, self.strings["not_user_or_channel"])
            return
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
                stars = [gift["sum"] for gift in user_gifts[0]["gifts"]]
                text += self.strings["giftline"].format(user_gifts[3][1], sum(stars))
                gifts = ""
                for gift in user_gifts[0]["gifts"]:
                    gifts += self.strings["gift"].format(gift["count"], gift["emoji"], gift["sum"])
                text += self.strings["exp"].format(gifts)
            try:
                await utils.answer(message, text)
            except DocumentInvalidError:
                await utils.answer(message, self.strings["docerror"].format(
                        "Limit: " + str(self.config["limit"]) + "\n"
                        + "Peer: " + str(id)
                    )
                )
        else:
            await utils.answer(message, self.strings["doesnthave"].format(name))

    async def _get_gifts(self, username, parameters):
        gifts = [{
            "nfts": [],
            "gifts": [],
        }]
        nft_count = 0
        gifts_count = 0
        try:
            gifts_info = await self.client(GetSavedStarGiftsRequest(peer=username, offset='', limit=int(self.config["gift_limit"]), **parameters))
            if int(self.config["gift_limit"]) > 100:
                if self.config["gift_limit"] < gifts_info.count:
                    count = self.config["gift_limit"]
                else:
                    count = gifts_info.count
                hundreds = count // 100
                remainder = count % 100
                limits = [*(100 for _ in range(hundreds-1)), *((remainder,) if remainder else ())]
                offsets = [100*i for i in range(1, hundreds + 1)]
                for limit, offset in zip(limits, offsets):
                    await asyncio.sleep(0.4)
                    next_offset = await self.client(GetSavedStarGiftsRequest(peer=username, offset=str(offset).encode(), limit=limit, **parameters))
                    gifts_info.gifts.extend(next_offset.gifts)
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
                    st_id = str(gift.gift.sticker.id).replace("5231003994519794860", "5253982443215547954").replace("5465502401358226185", "5298801741209299033").replace("5384540360863150750", "5413732008033543033") # < - jst dumpfix to avoid DocumentInvalidError
                    gift_exists = False
                    for gft in gifts[0]["gifts"]:
                        if st_id in gft["emoji"]:
                            gft["count"] += 1
                            gft["sum"] += gift.gift.stars
                            gift_exists = True
                            break
                    if gift_exists: continue
                    gifts[0]["gifts"].append({
                        "emoji": "<emoji document_id={}>{}</emoji>".format(st_id, gift.gift.sticker.attributes[1].alt),
                        "stars": f"<code>{gift.gift.stars}</code>" + " <emoji document_id=5951810621887484519>⭐️</emoji>",
                        "sum": gift.gift.stars,
                        "count": 1,
                    })
        gifts.append(shown)
        gifts.append([nft_count, gifts_count])
        return gifts
    
    @loader.command(ru_doc="[ссылка/gift-id] посмотреть информацию о подарке")
    async def gift(self, message):
        """[link/gift-id] view gift info"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["noargs"])
            return
            
        slug = args
        if "t.me/nft/" in args:
            slug = args.replace("https://t.me/nft/", "").replace("http://t.me/nft/", "").replace("t.me/nft/", "")
        
        slug = slug.split()[0].split('?')[0]
        
        if not slug:
            await utils.answer(message, self.strings["noargs"])
            return

        try:
            res = await self.client(GetUniqueStarGiftRequest(slug=slug))
        except Exception as e:
            if "STARGIFT_SLUG_INVALID" in str(e):
                await utils.answer(message, self.strings["gifterr"])
                return
            raise

        owner = res.users[0] if res.users else None
        if owner:
            first_name = getattr(owner, "first_name", "") or ""
            last_name = getattr(owner, "last_name", "") or ""
            owner_display_name = f"{first_name} {last_name}".strip() or "Unknown"
            if getattr(owner, "username", None) or (getattr(owner, "usernames", None) and len(owner.usernames) > 0):
                username = owner.username if getattr(owner, "username", None) else owner.usernames[0].username
                owner_str = f'<emoji document_id=5275979556308674886>👤</emoji> <b>Owner</b>: <a href="https://t.me/{username}">{owner_display_name}</a> (id: <code>{owner.id}</code>)'
            else:
                owner_str = f'<emoji document_id=5275979556308674886>👤</emoji> <b>Owner</b>: {owner_display_name} (id: <code>{owner.id}</code>)'
        elif getattr(res.gift, "owner_name", None):
            owner_display_name = res.gift.owner_name
            owner_str = f'<emoji document_id=5275979556308674886>👤</emoji> <b>Owner</b>: {owner_display_name}'
        else:
            owner_str = f'<emoji document_id=5275979556308674886>👤</emoji> <b>Owner</b>: Unknown'

        lines = [owner_str]

        for g in res.gift.attributes:
            if hasattr(g, "name"):
                if isinstance(g, StarGiftAttributeModel):
                    attr_type = f'<emoji document_id="{res.gift.attributes[0].document.id}">🎁</emoji> <b>Model</b>'
                elif isinstance(g, StarGiftAttributePattern):
                    attr_type = "<emoji document_id=5253944419870062295>🍃</emoji> <b>Pattern</b>"
                elif isinstance(g, StarGiftAttributeBackdrop):
                    attr_type = "<emoji document_id=5764899533565729469>🎨</emoji> <b>Background</b>"
                else:
                    attr_type = "Attribute"
                lines.append(f"{attr_type}: <code>{g.name}</code> (<code>{getattr(g, 'rarity_permille', 0)/10:.1f}</code>%)")

        lines.append(f"<emoji document_id=6007817446398890097>📝</emoji> <b>Issued</b>: <code>{res.gift.availability_issued}</code> / <code>{res.gift.availability_total}</code>")
        
        if hasattr(res.gift, 'value_amount') and hasattr(res.gift, 'value_currency'):
            lines.append(f"<emoji document_id=6014655953457123498>💱</emoji> <b>Price</b>: <code>{res.gift.value_amount // 100}</code> {res.gift.value_currency}")

        result = "\n".join(lines)
        await utils.answer(message, f'<a href="t.me/nft/{slug}">\u200f</a><blockquote>{result}</blockquote>', link_preview=True, invert_media=True)

__version__ = v