#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

# meta developer: @ZetGo
import asyncio, herokutl, math, io
from herokutl.tl.types import MessageService
from herokutl.tl.functions.channels import GetFullChannelRequest
from .. import loader, utils

CHECK_DELAY = 0.7
SCAM_DELAY = 1
@loader.tds
class SafeBase(loader.Module):
    """Небольшой инструментарий для модератора сейфбазы"""
    strings = {
            "name": "SafeBase",
            "noargs": "<emoji document_id=5019523782004441717>❌</emoji> <b>Команда введена без достаточного количества аргументов</b>",
            "part_collect": "<emoji document_id=5361756993876954306>⌛️</emoji> <b>Сбор информации об участниках...</b>",
            "additional": "<emoji document_id=5361756993876954306>⌛️</emoji> <b>Количество учатсников не совпало с реальным. Получение информации из последних {} сообщений. Это займёт ~{} сек.</b>",
            "checking_users": "<emoji document_id=5364035851984603413>💪</emoji> <b>Проверяю наличие участников в скам базе...\nЭто займёт ~{} сек.</b>",
            "all_in_base": "<emoji document_id=5361900011992942703>🥇</emoji> <b>Все участники @{} уже находятся в базе</b>",
            "part_list": "<emoji document_id=5361940169937158185>🥇</emoji> <b>Список участников группы @{}:</b>\n<blockquote expandable>{}</blockquote>",
            "file_part_list": "<emoji document_id=5361940169937158185>🥇</emoji> <b>Список участников группы @{}",
            "stop_cycle": "Вы можете остановить выполнение команды",
            "stop": "🛑 Остановить",
            "no_shct": "<emoji document_id=5019523782004441717>❌</emoji> <b>Шортката {} не существует</b>",
            "answer_file": "<emoji document_id=5019523782004441717>❌</emoji> <b>Вы должны ответить на файл!</b>",
            "no_ids": "<emoji document_id=5019523782004441717>❌</emoji> <b>В файле нет id людей</b>",
            "inv_shct": """<emoji document_id=5019523782004441717>❌</emoji> <b>Шорткат установлен неверно. Пример правильной команды:</b>
<code>.addscam scamgroup /scam {account} 2 Участник скам-тимы {link}</code>""",
            "shct_set": "<emoji document_id=5361940169937158185>🥇</emoji> <b>Шорткат <code>{}</code> установлен!</b>",
            "shct_rm": "<emoji document_id=5361940169937158185>🥇</emoji> <b>Шорткат <code>{}</code> удалён!</b>",
            "entr_to_base": "<emoji document_id=5364035851984603413>💪</emoji> <b>Заношу в базу {} человек...</b>",
            "succes": "<emoji document_id=5361940169937158185>🥇</emoji> <b>Успешно занёс!</b>",
        }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "check_chat_id",
                7246450592,
                "Чат с @SafeBase_checkbot (установите id чата,"
                " где находится бот, если не хотите засорять личку"
                " с ним)",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "msgs_limit",
                1000,
                "Лимит собираемых сообщений чата (влияет на время )",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "send_scam_chat",
                7246450592,
                "Чат, куда будут отправлены команды для заноса человека в базу",
            ),
        )

    async def client_ready(self):
        if not self.get("shortcuts", {}):
            self.set(
                key="shortcuts",
                value=dict()
            )
        return

    def get_messages_time(self, msgs):
        R = math.ceil(msgs / 100)
        if msgs > 3000:
            mraz = 1 + 0.00005 * (msgs - 3000)
        else:
            mraz = 1
        scnds = R * 0.5 * mraz
        return scnds
    
    async def _stop_getlist(self, call):
        await call.delete()
        self.getlist_c = False

    @loader.command()
    async def getlist(self, message):
        """[group id/username] (file/message) получить список участников группы либо в файле, либо в сообщении"""
        args = utils.get_args(message)
        if len(args):
            if len(args) < 2:
                args.append("message")
        else:
            return await utils.answer(message, self.strings["noargs"])
        group, output = args[:2]
        group = group.replace("@", "")
        group = int(group) if group.isdigit() else group
        self.client: herokutl.TelegramClient
        entity = await self.client(GetFullChannelRequest(group))

        all_users = [u for u in (await self.client.get_participants(group))]
        ids = set()

        self.getlist_c = True
        form = await self.inline.form(
            self.strings["stop_cycle"],
            message.chat_id,
            reply_markup={
                "text": self.strings["stop"],
                "callback": self._stop_getlist,
            }
        )

        await utils.answer(message, self.strings["part_collect"])
        if len(all_users) != entity.full_chat.participants_count:
            limit = min(self.config["msgs_limit"], (await self.client.get_messages(group, 0, search="+")).total)
            await utils.answer(message, self.strings["additional"].format(
                    self.config["msgs_limit"],
                    self.get_messages_time(self.config["msgs_limit"])
                )
            )
            async for msg in self.client.get_messages(group, limit=limit):
                if self.getlist_c:
                    if msg.sender and not getattr(msg.sender, "bot", True):
                        ids.add(msg.sender.id)
                else:
                    return await message.delete()

        ids |= {us.id for us in all_users if not us.bot}

        ids.discard(self.client.tg_id)

        await utils.answer(message, self.strings["checking_users"].format(
                (CHECK_DELAY + 0.5) * len(ids)
            )
        )
        
        for user in ids.copy():
            if self.getlist_c:
                async with self.client.conversation(self.config["check_chat_id"], exclusive=False) as conv:
                    await conv.send_message(f"чек {user}")
                    resp = await conv.get_response()
                    if not "нет записей" in resp.text or not "Администратором" in resp.text:
                        ids.discard(user)
                    await asyncio.sleep(CHECK_DELAY)
            else:
                return await message.delete()

        text = "\n".join(map(str, ids))

        await form.delete()

        if output == "message":
            await utils.answer(message, self.strings["part_list"].format(
                    group,
                    text
                )
            )
        else:
            file = io.BytesIO(text.encode())
            file.name = f"participants_{entity.full_chat.id}.txt"
            await utils.answer(message, self.strings["file_part_list"].format(group), file=file)

    @loader.command()
    async def scam(self, message):
        """[имя шортката] [id/file] [ссылка на доказательства] шорткат для заноса человека в скамеров"""
        args = utils.get_args(message)
        if not args or len(args) < 2:
            return await utils.answer(message, self.strings["noargs"])
        reply = await message.get_reply_message()
        reply = reply if not isinstance(reply, MessageService) else None
        if len(args) == 2:
            if not reply:
                return await utils.answer(message, self.strings["noargs"])
            
            shortcut, account = args
            link = reply.link()
        else:
            shortcut, account, link = args

        shortcuts = self.get("shortcuts", {})
        if not shortcut in shortcuts:
            return await utils.answer(message, self.strings["no_shct"].format(shortcut))

        ids = []
        if account == "file":
            if not reply or reply.media is None:
                return await utils.answer(message, self.strings["answer_file"])
            file = (await reply.download_media(bytes)).decode()
            lines = [x for x in file.splitlines() if x.strip().isdigit()]
            ids.extend(lines)
        else: 
            account = int(account)
            ids.append(account)

        if not ids:
            return await utils.answer(message, self.strings["no_ids"])
        
        await utils.answer(message, self.strings["entr_to_base"].format(len(ids)))
        
        for acc_id in ids:
            await self.client.send_message(
                self.config["send_scam_chat"],
                shortcuts[shortcut].format(
                    account=acc_id,
                    link=link,
                )
            )
            await asyncio.sleep(SCAM_DELAY)
        
        await utils.answer(message, self.strings["succes"])
    
    @loader.command()
    async def addscam(self, message):
        """[имя шортката] [строка]

        Пример:
        .addscam scamgroup /scam {account} 2 Участник скам-тимы {link}

        При вызове .scam scamgroup 1226061707 https://t.me/cht/25
        отправит в чат:
        /scam 1226061707 2 Участник скам-тимы https://t.me/cht/25
        """
        args = utils.get_args_raw(message).split(maxsplit=1)
        if len(args) != 2:
            return await utils.answer(message, self.strings["noargs"])
        
        if "{account}" not in args[1] or "{link}" not in args[1]:
            return await utils.answer(message, self.strings["inv_shct"])

        shortcuts = self.get("shortcuts", {})
        shortcuts[args[0]] = args[1]
        self.set("shortcuts", shortcuts)

        await utils.answer(message, self.strings["shct_set"].format(args[0]))

    @loader.command()
    async def delscam(self, message):
        """[имя шортката] удалить шорткат"""
        args = utils.get_args(message)
        if not args:
            return await utils.answer(message, self.strings["noargs"])
        name = args[0]

        shortcuts = self.get("shortcuts", {})
        if not name in shortcuts:
            return await utils.answer(message, self.strings["no_shct"].format(name))
        else:
            shortcuts.pop(name)
            self.set("shortcuts", shortcuts)

        await utils.answer(message, self.strings["shct_rm"].format(name))