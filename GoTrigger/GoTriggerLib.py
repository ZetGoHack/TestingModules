# ░░░███░███░███░███░███
# ░░░░░█░█░░░░█░░█░░░█░█
# ░░░░█░░███░░█░░█░█░█░█
# ░░░█░░░█░░░░█░░█░█░█░█
# ░░░███░███░░█░░███░███

# meta developer: @ZetGo
# requires: gotriggerlib

import base64
from dataclasses import dataclass
from typing import ClassVar, Literal

import gotriggerlib
from herokutl.errors import FileReferenceExpiredError, FileReferenceInvalidError
from herokutl.extensions import BinaryReader
from herokutl.tl.types import TypeMessageMedia
from telethon.tl.custom import Message

from .. import loader, utils

__version__ = (0, 2, 1)


@dataclass
class MessageMedia(gotriggerlib.Exportable):
    """Один медиа-файл, зашитый в реакцию напрямую (base64), с рефрешем на протухшую ссылку"""

    display_name: ClassVar[str] = "media"

    media: str
    media_type: str
    chat_id: int
    message_id: int

    async def refresh(self, client):
        fresh = await client.get_messages(self.chat_id, ids=self.message_id)
        self.media = base64.b64encode(bytes(fresh.media)).decode()
        return self.get()

    def get(self) -> TypeMessageMedia:
        return BinaryReader(base64.b64decode(self.media)).tgread_object()

    @staticmethod
    def encode(media: TypeMessageMedia) -> str:
        return base64.b64encode(bytes(media)).decode()

    def describe(self) -> str:
        return f"{self.media_type} media from t.me/c/{self.chat_id}/{self.message_id}"

    @staticmethod
    def parse(message_with_media: Message) -> "MessageMedia | None":
        if message_with_media.media is None:
            return None

        media = MessageMedia.encode(message_with_media.media)
        media_type = message_with_media.media.__class__.__name__.removeprefix("MessageMedia")

        return MessageMedia(
            media, media_type, message_with_media.chat_id, message_with_media.id
        )


@dataclass
class MessageReaction(gotriggerlib.Reaction):
    """Готовая реакция "отправить сообщение" — общая для GoTrigger и любого стороннего Trigger'а"""

    display_name: ClassVar[str] = "send_message"

    text: str = ""
    media: MessageMedia | None = None
    reply_to: Literal["trigger", "trigger_reply"] | int | None = "trigger_reply"
    send_to_chat_id: int | None = None

    async def send(self, message: Message) -> None:
        kwargs = {}
        if self.reply_to == "trigger":
            fun = message.reply
        elif self.reply_to == "trigger_reply":
            fun = message.respond
        else:
            fun = message.client.send_message
            kwargs = {
                "entity": self.send_to_chat_id or message.chat_id,
                "reply_to": self.reply_to,
            }

        media = self.media.get() if self.media else None

        try:
            await fun(self.text, file=media, **kwargs)
        except (FileReferenceExpiredError, FileReferenceInvalidError):
            await fun(self.text, file=await self.media.refresh(message.client), **kwargs)

    def describe(self) -> str:
        preview = utils.escape_html(self.text[:40]) or (
            self.media.describe() if self.media else "empty"
        )
        return f"send {preview} -> {self.reply_to}"

    @staticmethod
    def parse(
        message: Message,
        media_message: Message | None = None,
        reply_to: Literal["trigger", "trigger_reply"] | int | None = "trigger_reply",
        send_to_chat_id: int | None = None,
    ) -> "MessageReaction":
        """Собирает реакцию из отвеченного сообщения: текст + опционально медиа из другого сообщения"""
        return MessageReaction(
            text=message.text,
            media=MessageMedia.parse(media_message) if media_message else None,
            reply_to=reply_to,
            send_to_chat_id=send_to_chat_id,
        )


gotriggerlib.validate_registry()


class GoTriggerLib(loader.Library):
    """Реестр Trigger'ов от сторонних модулей для GoTrigger + готовые MessageMedia/MessageReaction.

    ⚠️ Match/Reaction/Trigger наследуются напрямую через `import gotriggerlib`, а не через
    self.lookup(...) — тело класса выполняется до того, как self.lookup станет доступен.
    """

    Match = gotriggerlib.Match
    Reaction = gotriggerlib.Reaction
    Trigger = gotriggerlib.Trigger
    MessageMedia = MessageMedia
    MessageReaction = MessageReaction

    async def init(self):
        self._triggers: dict[str, tuple[str, gotriggerlib.Trigger]] = {}

    def register_trigger(self, trigger: gotriggerlib.Trigger, owner: str) -> None:
        """Вызывать из client_ready поставщика; перерегистрация по тому же имени — обновление"""
        self._triggers[trigger.name] = (owner, trigger)

    def unregister_trigger(self, name: str) -> None:
        """Вызывать из on_unload поставщика"""
        self._triggers.pop(name, None)

    @property
    def triggers(self) -> list[gotriggerlib.Trigger]:
        return [trigger for _, trigger in self._triggers.values()]

    def owner_of(self, name: str) -> str | None:
        entry = self._triggers.get(name)
        return entry[0] if entry else None

    def active_types(self) -> dict[type, str]:
        """{Match/Reaction-класс: владелец}, посчитано по текущим триггерам"""
        return {
            type(obj): owner
            for owner, trigger in self._triggers.values()
            for obj in (*trigger.matches, *trigger.reactions)
        }
