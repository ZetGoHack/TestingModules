#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

# meta developer: @ZetGo

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

        toplist: list = self.channels_top_cache.setdefault(channel.id, {
            "chat": chat.id,
            "channel_messages_ids": [],
            "top_users": {},
            "last_message_id": 1,
        })

        if toplist["chat"] != chat.id:
            toplist["chat"] = chat.id
            toplist["channel_messages_ids"] = []
            toplist["last_message_id"] = 1

        offset_id = toplist["last_message_id"] + 1
        async for msg in self.client.iter_messages(chat.id, offset_id=offset_id, reverse=True):
            msg: Message
            if msg.id > toplist["last_message_id"]:
                toplist["last_message_id"] = msg.id

            if utils.get_entity_id(msg.from_id) == channel.id:
                toplist["channel_messages_ids"].append(msg.id)
                continue

            if not msg.reply_to:
                continue

            if msg.reply_to.reply_to_top_id in toplist["channel_messages_ids"]:
                if msg.sender_id in toplist["top_users"]:
                    toplist["top_users"][msg.sender_id]["count"] += 1
                    toplist["top_users"][msg.sender_id]["words_count"] += len((msg.text or "").split())
                    toplist["top_users"][msg.sender_id]["letters_count"] += len((msg.text or "").replace(" ", ""))
                else:
                    toplist["top_users"][msg.sender_id] = {
                        "count": 1,
                        "words_count": len((msg.text or "").split()),
                        "letters_count": len((msg.text or "").replace(" ", "")),
                    }

        self.channels_top_cache[channel.id] = toplist

        
