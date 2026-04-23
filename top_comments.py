#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

from telethon.tl.custom import Message
from telethon.tl.types import Channel, PeerChannel

from .. import loader, utils
from ..pointers import PointerDict

@loader.tds
class TopCommentsMod(loader.Module):
    strings = {
        "name": "TopComments",
    }
    strings_ru = {
        "not_chat": "<b>Команда введена не в канале/группе обсуждения канала. Модуль не может посчитать топ комментариев в лс и обычных чатах</b>",
        "no_linked_chat": "<b>К вашему каналу не привязан чат. Модуль не может составить топ комментариев без него</b>",
    }
    
    async def client_ready(self):
        self.channels_top_cache: "PointerDict" = self.pointer("channels_top_cache", {})
    
    @loader.command()
    async def topcomments(self, message: Message):
        """"""
        args = utils.get_args(message)
        chat_id = utils.get_chat_id(message)
        
        if not isinstance(message.peer_id, PeerChannel):
            return await utils.answer(message, self.strings["not_chat"])
        
        full_channel = await self.client.get_fullchannel(message.peer_id)

        if not full_channel.linked_chat_id:
            return await utils.answer(message, self.strings["no_linked_chat"])

        chats = full_channel.chats
        channel = next(chat for chat in chats if isinstance(chat, Channel) and not chat.megagroup)
        chat = next(chat for chat in chats if isinstance(chat, Channel) and chat.megagroup)
