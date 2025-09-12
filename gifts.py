#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]
v = ("oooo", "kaa", "kkk")
# meta developer: @nullmod
# scope: heroku_min 1.7.2
# scope: hikka_min 1.7.2

# -      main      - #
from .. import loader, utils
# -      func      - #
import asyncio
import time
from herokutl.tl.functions.payments import GetSavedStarGiftsRequest, GetUniqueStarGiftRequest
# -      types     - #
from herokutl.tl.types import Channel, SavedStarGift, StarGift, StarGiftUnique, User
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
            params["exclude_saved"] = True
            
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
                    count = self.config["gifts_limit"]
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
        args = utils.get_args_raw(message).replace("t.me/nft/", "").split()
        if not args:
            await utils.answer(message, self.strings["noargs"])
            return
        if len(args) > 1:
            await utils.answer(message, self.strings["toomany"])
            return
        try:
            nft = await self.client(GetUniqueStarGiftRequest(slug=args[0]))
        except Exception as e:
            if "STARGIFT_SLUG_INVALID" in str(e):
                await utils.answer(message, self.strings["gifterr"])
                return
        text = f"<a href='t.me/nft/{args[0]}'>\u200f</a>Окак (команда в процессе разработки не нужно это того самое)"
        await utils.answer(message, text)#, invert_media=True)

    async def _split_nfts(self, gifts):
        strings = []
        for gift in gifts:
            strings.append(
                self.strings["nft"]
            )

        
__version__ = v

# nft = UniqueStarGift(
#  gift=StarGiftUnique(
#   id=5821049767035142988,
#   title='Trapped Heart',
#   slug='TrappedHeart-19095',
#   num=19095,
#   attributes=[
#    StarGiftAttributeModel(
#     name='Silver Luxe',
#     document=Document(
#      id=5402510413835302585,
#      access_hash=-6433169821750188931,
#      file_reference=b'\x00hC\xf1\xe3v\x9b\xcc\x11\x03:\xcdy\x1a\x12GZ$\x02\xbe\x1b',
#      date=datetime.datetime(2024, 12, 16, 1, 40, 52, tzinfo=datetime.timezone.utc),
#      mime_type='application/x-tgsticker',
#      size=18196,
#      dc_id=2,
#      attributes=[
#       DocumentAttributeImageSize(
#        w=512,
#        h=512
#       ),
#       DocumentAttributeCustomEmoji(
#        alt='🖤',
#        stickerset=InputStickerSetID(
#         id=1260742488159682581,
#         access_hash=-9108761878258913401
#        ),
#        free=False,
#        text_color=False
#       ),
#       DocumentAttributeFilename(
#        file_name='AnimatedSticker.tgs'
#       ),
#      ],
#      thumbs=[
#       PhotoPathSize(
#        type='j',
#        bytes=b'\x1b\t\xb2\x04\xdc\\b~F\x07K\x01G\x02[Ct\x87\x03F\x08\x86\x06PF\x90`\x91g\x81EJVMZP\\gtF\x06F\x08KGa\x88e\x80FN\x94L\x9c`\x8de\x96G\x06\x9aK\x06\x84n\x81I\x04JN\x00CLpp`v\x84B\xb1\xad\x88\x00\xb0\xa2\x84\x87\x04G\x8a\x02\\\x8aG\xa3m\xa9k\x88\x83\x8f\xa0\x95\xa8\x98\x9d\xbc\xae\x89\x06\xb6\xa4\x87\x87\x05\x85\x8a\tJ\x88C\xaca\xb1U\x85\x8eW\x95\\\x9fF\x8eI\x9fK\xaeE\xadC\x89\x08\x8d\x8e\x01\x88\x97\x9f\x8e\x9b\x9eB\x89S\x80W\x81C\x80D\x85E\x87S\x9e^\x86\x08X\x8a\x03\x81\x8b\x82\x9a\x87\xa3\x84\x89\x9e\x9b\x9a\xa5H\x95aWf\\HHWMaOhGI\x01\x89L\x02\xa3G\x86M\x8fU\x94'
#       ),
#       PhotoSize(
#        type='m',
#        w=128,
#        h=128,
#        size=7734
#       ),
#      ],
#      video_thumbs=[
#      ]
#     ),
#     rarity_permille=20
#    ),
#    StarGiftAttributePattern(
#     name='Beetle',
#     document=Document(
#      id=5440627552802592767,
#      access_hash=-642335644292992144,
#      file_reference=b'\x00hC\xf1\xe3\xc7:l,f\xff\xe7\xac\x94 qc\x07\xb1\xe7\xcd',
#      date=datetime.datetime(2024, 12, 28, 11, 8, 38, tzinfo=datetime.timezone.utc),
#      mime_type='application/x-tgsticker',
#      size=1265,
#      dc_id=2,
#      attributes=[
#       DocumentAttributeImageSize(
#        w=512,
#        h=512
#       ),
#       DocumentAttributeCustomEmoji(
#        alt='🪲',
#        stickerset=InputStickerSetID(
#         id=1983652455501529109,
#         access_hash=3008396452719838757
#        ),
#        free=False,
#        text_color=True
#       ),
#       DocumentAttributeFilename(
#        file_name='AnimatedSticker.tgs'
#       ),
#      ],
#      thumbs=[
#       PhotoPathSize(
#        type='j',
#        bytes=b'\t\x05\xaf\x07\xdcG\x04c\xa5O\x05\xacT\x05\x86k[\x92j\x9cE\x83f\x8cg\x91C\x8eS\x86\x08g\x9daF\x07\x8e\x06L\x08\x8e\x08P\x04\x80JTIZQKOPl`vYOG\x02\x8bvk\x83I\x89S\x91W\xa3Q\x88\x04\x8c\t\x8d\x08\x88\x04\x8cJNIWTHIeH\x02eH\x03\x87H\x95J\x9fJ\xbf\x80\x83\xbc\xb9\xb9\x93A\xa8\x84\xbb\x81\x8fBNI\x08\xbcs\x86\x84V\x87\x04`\x88\x06G\x88Y\x88^\x8eD\x86\x8b\x8a\x91\x8e\xa8\x9d\x8a\x06L\t\x8d\x08H\x04\xa9\xbaX\xaco\xbaR\x8bV\xabd\xbaF\x87V\x85V\x8d\x82\xa4\x92\x08\x8a\x00\x8e\x05\x90\x08T\xa1bUda\x81EePjTPLWbhkQH\x83\xa9\x91\xb4\x90\x8c\x88\x02\x8f\x08\xa1\x91\x01_\x88mM\x00uK\x04Z\xb3J\x04\x92\x00J\x05\xb4\x80t\x81J\x04CO\x06AW\x83I\x02FG\x00U\xb3\x8c\x99\x05L\x9c\x00b\xa4J\x01J\x05J\x01J\x05T\xa2O\x8a\x01o\x8b\x03'
#       ),
#       PhotoSize(
#        type='m',
#        w=128,
#        h=128,
#        size=2970
#       ),
#      ],
#      video_thumbs=[
#      ]
#     ),
#     rarity_permille=2
#    ),
#    StarGiftAttributeBackdrop(
#     name='Satin Gold',
#     backdrop_id=19,
#     center_color=12557127,
#     edge_color=9271097,
#     pattern_color=6109952,
#     text_color=16704681,
#     rarity_permille=15
#    ),
#    StarGiftAttributeOriginalDetails(
#     recipient_id=PeerUser(
#      user_id=1226061708
#     ),
#     date=datetime.datetime(2024, 10, 29, 21, 24, 56, tzinfo=datetime.timezone.utc),
#     sender_id=PeerUser(
#      user_id=7212151458
#     ),
#     message=None
#    ),
#   ],
#   availability_issued=23355,
#   availability_total=26407,
#   owner_id=PeerUser(
#    user_id=1226061708
#   ),
#   owner_name=None,
#   owner_address=None,
#   gift_address=None,
#   resell_stars=None
#  ),
#  users=[
#   User(
#    id=1226061708,
#    is_self=True,
#    contact=True,
#    mutual_contact=True,
#    deleted=False,
#    bot=False,
#    bot_chat_history=False,
#    bot_nochats=False,
#    verified=False,
#    restricted=False,
#    min=False,
#    bot_inline_geo=False,
#    support=False,
#    scam=False,
#    apply_min_photo=False,
#    fake=False,
#    bot_attach_menu=False,
#    premium=True,
#    attach_menu_enabled=False,
#    bot_can_edit=False,
#    close_friend=False,
#    stories_hidden=False,
#    stories_unavailable=True,
#    contact_require_premium=False,
#    bot_business=False,
#    bot_has_main_app=False,
#    access_hash=7904001167064024655,
#    first_name='\u200f\u2067\u2067\u2067\u2067 стик\u2067Пуши',
#    last_name=None,
#    username=None,
#    phone='&lt;phone&gt;',
#    photo=UserProfilePhoto(
#     photo_id=5332626249799039002,
#     dc_id=2,
#     has_video=False,
#     personal=False,
#     stripped_thumb=b'\x01\x08\x08\x81\xdb\x01O;\x8eh\xa2\x8ab?'
#    ),
#    status=UserStatusOnline(
#     expires=datetime.datetime(2025, 6, 7, 8, 6, 19, tzinfo=datetime.timezone.utc)
#    ),
#    bot_info_version=None,
#    restriction_reason=[
#    ],
#    bot_inline_placeholder=None,
#    lang_code=None,
#    emoji_status=EmojiStatusCollectible(
#     collectible_id=6032857814404170672,
#     document_id=5425029528663646777,
#     title='Eternal Rose #2438',
#     slug='EternalRose-2438',
#     pattern_document_id=5308032304533223255,
#     center_color=13413185,
#     edge_color=9993010,
#     pattern_color=7355392,
#     text_color=16770475,
#     until=None
#    ),
#    usernames=[
#     Username(
#      username='ZetGo',
#      editable=True,
#      active=True
#     ),
#     Username(
#      username='tgfurr',
#      editable=False,
#      active=True
#     ),
#    ],
#    stories_max_id=None,
#    color=PeerColor(
#     color=11,
#     background_emoji_id=5368841297618547822
#    ),
#    profile_color=PeerColor(
#     color=15,
#     background_emoji_id=5202021924573561302
#    ),
#    bot_active_users=None,
#    bot_verification_icon=None,
#    send_paid_messages_stars=None
#   ),
#   User(
#    id=7212151458,
#    is_self=False,
#    contact=True,
#    mutual_contact=True,
#    deleted=False,
#    bot=False,
#    bot_chat_history=False,
#    bot_nochats=False,
#    verified=False,
#    restricted=False,
#    min=False,
#    bot_inline_geo=False,
#    support=False,
#    scam=False,
#    apply_min_photo=True,
#    fake=False,
#    bot_attach_menu=False,
#    premium=False,
#    attach_menu_enabled=False,
#    bot_can_edit=False,
#    close_friend=False,
#    stories_hidden=False,
#    stories_unavailable=True,
#    contact_require_premium=False,
#    bot_business=False,
#    bot_has_main_app=False,
#    access_hash=-795669221529757911,
#    first_name='Мими 💖 основа @nekoFwU',
#    last_name=None,
#    username='Last_Mimi',
#    phone='37060444231',
#    photo=UserProfilePhoto(
#     photo_id=5967736142033962458,
#     dc_id=4,
#     has_video=False,
#     personal=False,
#     stripped_thumb=b'\x01\x08\x08h\x8e]\xc1\xfe}\xfb\xb9\x18\xe3\x14QE$S?'
#    ),
#    status=UserStatusOffline(
#     was_online=datetime.datetime(2025, 6, 6, 16, 9, 37, tzinfo=datetime.timezone.utc)
#    ),
#    bot_info_version=None,
#    restriction_reason=[
#    ],
#    bot_inline_placeholder=None,
#    lang_code=None,
#    emoji_status=None,
#    usernames=[
#    ],
#    stories_max_id=None,
#    color=None,
#    profile_color=None,
#    bot_active_users=None,
#    bot_verification_icon=None,
#    send_paid_messages_stars=None
#   ),
#  ]
# )
