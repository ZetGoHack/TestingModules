#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

__version__ = (1, 0, 0)

import re

from telethon.tl.custom import Message

from .. import loader, utils

SILERO_USERNAME = "@silero_voice_bot"
SUB_PROMPT_RE = re.compile(r"Подпишись на канал новостей бота: @([a-zA-Z][a-zA-Z0-9_]{4,30})")

@loader.tds
class SileroTTSMod(loader.Module):
    """Бубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубубу"""
    strings = {
        "name": "SileroTTS",
        "no_args": "Нечего обрабатывать. Вы не указали текст для озвучки",
        "no_audio": "Не удалось озвучить: в ответе от бота не оказалось файла",
        "bot_is_not_responding": "Не удалось дождаться ответа от бота. Попробуйте позже",
        "processing": "Обрабатываю...",
        "sub": (
            "Для работы команды подпишитесь на @{channel}."
            "После подписки вы сможете пользоваться модулем и снова ввести команду <code>{command}</code>"
        ),
    }
    
    async def _process_tts(self, message: Message, tts_text: str, caption: str = ""):
        async with self.client.conversation(SILERO_USERNAME) as conv:
            for _ in range(2):
                await conv.send_message(tts_text)

                try:
                    result: Message = await conv.get_response()
                except TimeoutError:
                    return await utils.answer(message, self.strings["bot_is_not_responding"])

                await conv.mark_read()

                if _match := SUB_PROMPT_RE.search(result.text):
                    click = await result.click()

                    if click.message == "Вас нет в списке подписчиков.":
                        return await utils.answer(message, self.strings["sub"].format(channel=_match.group(1), command=message.message))

                    elif click.message == "Успешно!":
                        continue

                else:
                    break
        
        if not result.media:
            return await utils.answer(message, self.strings["no_audio"])
        
        if message.out:
            await message.delete()

        return await self.client.send_message(message.chat_id, caption, file=result.media, reply_to=getattr(message.reply_to, "reply_to_msg_id", None))


    @loader.command()
    async def tts(self, message: Message):
        """[текст] - озвучить текст"""
        text = utils.get_args_raw(message)

        if not text:
            return await utils.answer(message, self.strings["no_args"])

        return await self._process_tts(message, text)

    @loader.command()
    async def ttst(self, message: Message):
        """[текст для озвучки] / [подпись] - озвучить текст и оставить подпись под гс

        .ttst текст - оставит в подписи озвученный текст
        .ttst текст / подпись - оставит в подписи ваш собственный текст"""
        args = utils.get_args_html(message)

        if not args:
            return await utils.answer(message, self.strings["no_args"])
        
        if len(args := args.split("/", maxsplit=1)) < 2:
            text = args
            caption = ""
        else:
            text, caption = args

        return await self._process_tts(message, text, caption)

