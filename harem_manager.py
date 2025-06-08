__version__ = (1,0,0)
#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
# H:Mods Team [💎]

# -      main      - #
from .. import loader, utils
# -      func      - #
import asyncio
import logging
import time
import re
# -    func(tl)    - #
from telethon.tl.functions.chatlists import CheckChatlistInviteRequest, JoinChatlistInviteRequest, LeaveChatlistRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
# -      types     - #
from telethon.tl.types import InputChatlistDialogFilter, UpdateDialogFilter
# -      errors    - #
from telethon.errors import YouBlockedUserError, InviteRequestSentError
# -      end       - #

logger = logging.getLogger(__name__)

@loader.tds
class HaremManager(loader.Module):
    """Module for harem bots: Gif Harem, Waifu Harem, Horny Harem"""

    strings = {
        "name": "WaifuHarem"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "ab-horny",
                False,
                "Автобонус(/bonus, бонус за подписки, 'lights out')",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "interval-horny",
                4,
                "Интервал между автобонусом",
                validator=loader.validators.Float(2.0)
            ),
            loader.ConfigValue(
                "catch-horny",
                False,
                "Автоловля вайфу",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "ab-waifu",
                False,
                "Автобонус(/bonus, бонус за подписки, 'lights out')",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "interval-waifu",
                4,
                "Интервал между автобонусом",
                validator=loader.validators.Float(2.0)
            ),
            loader.ConfigValue(
                "ab-gif",
                False,
                "Автобонус(/bonus, бонус за подписки, 'lights out')",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "interval-gif",
                4,
                "Интервал между автобонусом",
                validator=loader.validators.Float(2.0)
            ),
            loader.ConfigValue(
                "catch-gif",
                False,
                "Автоловля вайфу",
                validator=loader.validators.Boolean(),
            ),
        )
    
    async def client_ready(self):
        self.harems = {
            "horny": "@Horny_GaremBot",
            "waifu": "@garem_chatbot",
            "gif": "@GIFgarem_bot"
        }
        self.cather_ids = []
        self.blockBot = False

    def _main_markup(self):
        return [
                [
                    {
                        "text": "[✔️] Horny Harem" if self.config["ab-horny"] else "[❌] Horny Harem",
                        "callback": self.callback_handler,
                        "args": ("horny",)
                    },
                    {
                        "text": "[✔️] Waifu Harem" if self.config["ab-waifu"] else "[❌] Waifu Harem",
                        "callback": self.callback_handler,
                        "args": ("waifu",)
                    },
                   ],
                   [
                    {
                        "text": "[✔️] Gif Harem" if self.config["ab-gif"] else "[❌] Gif Harem",
                        "callback": self.callback_handler,
                        "args": ("gif",)
                    }
                   ],
                   [
                    {
                        "text": "🔻 Закрыть",
                        "action": "close",
                    }
                   ]
               ]
        
    def _menu_markup(self, bot):
        markup = []
        markup.append([
                        {
                            "text": "[✔️] Автобонус" if self.config[f"ab-{bot}"] else "[❌] Автобонус", 
                            "callback": self.callback_handler,
                            "args": (f"ab-{bot}",)
                        }
                    ])
        if "waifu" not in bot:
            markup[0].append({
                                "text":"[✔️] Автоловля" if self.config[f"catch-{bot}"] else "[❌] Автоловля",
                                "callback":self.callback_handler,
                                "args": (f"catch-{bot}",)
                            })
        markup.append(
                [
                    {
                        "text":"🔁 Перезапустить автобонус",
                        "callback": self.callback_handler,
                        "args": (f"restart-{bot}",)
                    },
                ],
            )
        markup.append([
                    {
                        "text":"↩️ Назад", 
                        "callback":self.callback_handler,
                        "args": ("back",)
                    }
                ])

    async def _set_menu(self, message):
        await utils.answer(
            message=message,
            text="❤️ Выберите бота для управления\n\n<i>*✅ Означает, что автобонус включён</i>",
            reply_markup=self._main_markup()
        )

    async def callback_handler(self, call, data):
        if data == "back":
            await self._set_menu(call)
            return
        elif data.startswith("restart-"):
            bot = data.split("-")[-1]
            self._autobonus(self.harems[bot])
            return
        elif data.startswith("ab-"):
            bot = data.split("-")[-1]
            self.config[f"ab-{bot}"] = not self.config[f"ab-{bot}"]
            if self.config[f"ab-bot"]:
                if bot not in self.ab_ids:
                    self.ab_ids.append(bot)
            else:
                if bot in self.ab_ids:
                    self.ab_ids.remove(bot)
            await call.edit(reply_markup=self._menu_markup(bot))
        elif data.startswith("catch-"):
            bot = data.split("-")[-1]
            self.config[f"catch-{bot}"] = not self.config[f"catch-{bot}"]
            if self.config[f"catch-{bot}"]:
                if bot not in self.cather_ids:
                    self.cather_ids.append(bot)
            else:
                if bot in self.cather_ids:
                    self.cather_ids.remove(bot)
            await call.edit(reply_markup=self._menu_markup(bot))

    async def _autobonus(self, id):
        wait_boost = False
        async with self._client.conversation(id) as conv:
            try:
                await conv.send_message("/bonus")
            except YouBlockedUserError:
                await self.client(UnblockRequest(id))
                await conv.send_message("/bonus")
            try:
                r = await conv.get_response(timeout=5*60)
            except:
                tryings = 5
                while tryings > 0:
                    tryings -= 1
                    try:
                        r = await conv.get_response(5*60)
                        break
                    except:
                        pass
                if r is None:
                    logger.warning("Ответ от бота не получен. Вероятно, он снова лёг\n\nПерезапустите автобонус, когда бот очнётся")
                    self.config[f"ab-{id}"] = False
                    return
            self.set("ABonus_time", int(time.time()))
            if "Доступен бонус за подписки" in r.text:
                await conv.send_message("/start flyer_bonus")
                r = await conv.get_response()
                if "проверка пройдена" not in r.text:
                    to_leave, to_block, folders, chats_in_folders = [], [], [], []
                    wait_boost = False
                    if r.reply_markup:
                        a = r.buttons
                        for i in a:
                            for button in i: # каждая кнопка...
                                if button.url:
                                    alr = False # "уже зашёл"
                                    if "addlist/" in button.url: # добавление папок
                                        slug = button.url.split("addlist/")[-1]
                                        peers = await self.client(CheckChatlistInviteRequest(slug=slug))
                                        if peers:
                                            peers = peers.peers
                                            try:
                                                a = await self.client(JoinChatlistInviteRequest(slug=slug, peers=peers))
                                                chats_in_folders.append(peers) # для выхода
                                                for update in a.updates:
                                                    if isinstance(update, UpdateDialogFilter):
                                                        folder.append(InputChatlistDialogFilter(filter_id=update.id)) # для удаления папки
                                            except: pass
                                        continue
                                    if "t.me/boost" in button.url: # бустить не обязательно
                                        wait_boost = True
                                        continue
                                    if not bool(re.match(r"^https?:\/\/t\.me\/[^\/]+\/?$", button.url)): # дополнительные вложения отметаем
                                        continue
                                    if "t.me/+" in button.url: # приватные чаты
                                        try:
                                            a = await self.client(CheckChatInviteRequest(button.url.split("+")[-1]))
                                            if not hasattr(a, "request_needed") or not a.request_needed: # получить айди приватного чата/канала с приглашениями без входа невозможно
                                                pass
                                            else:
                                                url = button.url.split("?")[0] if "?" in button.url else button.url
                                                self.blockBot = True ######
                                                try:
                                                    await self.client(ImportChatInviteRequest(button.url.split("+")[-1]))
                                                except InviteRequestSentError: pass
                                                await asyncio.sleep(3)
                                                try:
                                                    entity = await self.client.get_entity(url)
                                                except ValueError:
                                                    try:
                                                        await asyncio.sleep(15)
                                                        entity = await self.client.get_entity(url)
                                                    except: 
                                                        self.blockBot = False
                                                        continue
                                                except:
                                                    pass
                                                self.blockBot = False
                                                alr = True
                                        except: continue
                                    url = button.url.split("?")[0] if "?" in button.url else button.url
                                    if not alr:
                                        try:
                                            entity = await self.client.get_entity(url)
                                        except:
                                            entity = (await self.client(ImportChatInviteRequest(button.url.split("+")[-1]))).chats[0] #gotten class Updates
                                            alr = True
                                    if hasattr(entity, "broadcast"):
                                        if not alr:
                                            await self.client(JoinChannelRequest(button.url))
                                            to_leave.append(entity.id)
                                        else:
                                            to_leave.append(entity.chat.id) if hasattr(entity,"chat") else to_leave.append(entity.id) if hasattr(entity,"id") else None
                                    elif hasattr(entity, "bot"):
                                        try:
                                            await self.client(UnblockRequest(entity.username))
                                        except: print("блин")
                                        await self.client.send_message(entity, "/start")
                                        to_block.append(entity.username)
                        flyer_messages = await self.client.get_messages(id, limit=1)
                        if wait_boost:
                            await asyncio.sleep(150)
                        for m in flyer_messages:
                            await asyncio.sleep(5)
                            await m.click()
                            await asyncio.sleep(5)
                        for folder, chats in zip(folders, chats_in_folders):
                            await self.client(LeaveChatlistRequest(peers=chats, chatlist=folder))
                        for bot in to_block:
                            await self.client(BlockRequest(bot))
                            await self.client.delete_dialog(bot)
                        for channel in to_leave:
                            try:
                                await self.client(LeaveChannelRequest(channel))
                            except Exception as e:
                                pass
                count = 0
                if not self.get("last_lout") or int(time.time()) - self.get("last_lout") > 43200:
                    while count <= 2:
                        await conv.send_message("/lout")
                        r = await conv.get_response()
                        if r.reply_markup:
                            m = await r.respond(".")
                            await self.lightsoutW(m,r)
                            await m.delete()
                            self.set("last_lout", int(time.time()))
                            count += 1
                        else:
                            break

    @loader.command()
    async def HaremManager(self, message):
        """Открыть меню управления"""
        await self._set_menu(message)
        await utils.answer(
            message=message,
            text="Выберите гарем для управления",
            reply_markup=self._main_markup()
        )