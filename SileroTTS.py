#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

__version__ = (0, 0, 1)

from telethon.tl.custom import Message

from .. import loader, utils

SILERO_USERNAME = "@silero_voice_bot"
SUB_PROMPT = "Подпишись на канал новостей бота: @silero_voice_news"

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
            "Для работы команды подпишитесь на @silero_voice_news."
            "После подписки вы сможете пользоваться модулем и снова ввести команду <code>{text}</code>"
        ),
    }
    
    async def _process_tts(self, message: Message, caption: str = ""):
        text = utils.get_args_raw(message)
        if not text:
            return await utils.answer(message, self.strings["no_args"])
        
        async with self.client.conversation(SILERO_USERNAME) as conv:
            await conv.send_message(text)
            try:
                result: Message = await conv.get_response()
            except TimeoutError:
                return await utils.answer(message, self.strings["bot_is_not_responding"])
            
        if SUB_PROMPT in result.text:
            return await utils.answer(message, self.strings["sub"])
        
        if not message.media:
            return await utils.answer(message, self.strings["no_audio"])

        if message.out:
            await message.delete()

        if message.is_reply:
            return await utils.answer(message, caption, file=result.media)



    @loader.command()
    async def tts(self, message: Message):
        """[текст] - озвучить текст"""

    @loader.command()
    async def ttst(self, message: Message):
        """[текст для озвучки] / [подпись] - озвучить текст и оставить подпись под гс

        .ttst текст - оставит в подписи озвученный текст
        .ttst текст / подпись - оставит в подписи ваш собственный текст"""
        pass

