# ░░░███░███░███░███░███
# ░░░░░█░█░░░░█░░█░░░█░█
# ░░░░█░░███░░█░░█░█░█░█
# ░░░█░░░█░░░░█░░█░█░█░█
# ░░░███░███░░█░░███░███

# meta developer: @ZetGo
# requires: python-dateutil

import base64
import logging
import re

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, time
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from typing import Literal
from zoneinfo import ZoneInfo

from herokutl.extensions import BinaryReader
from herokutl.errors import FileReferenceExpiredError, FileReferenceInvalidError
from herokutl.tl.types import TypeMessageMedia
from herokutl.tl.custom import Message

from .. import loader, utils

logger = logging.getLogger(__name__)

WEEKDAYS = (MO, TU, WE, TH, FR, SA, SU)


class Condition(ABC):
    @abstractmethod
    def matches(self, dt: datetime) -> bool: ...


@dataclass
class TimeCond(Condition):
    conditions: tuple[Condition, ...]

    def __init__(self, *conditions: Condition):
        self.conditions = conditions

    def matches(self, dt: datetime) -> bool:
        return all(c.matches(dt) for c in self.conditions)


@dataclass
class Weekday(Condition):
    days: set[int]

    def matches(self, dt):
        return dt.weekday() in self.days


@dataclass
class DayOfMonth(Condition):
    days: set[int]

    def matches(self, dt):
        return dt.day in self.days


@dataclass
class LastDayOfMonth(Condition):
    def matches(self, dt):
        return dt.day == (dt + relativedelta(day=31)).day


@dataclass
class NthWeekday(Condition):
    weekday: int
    n: int
    period: str = "month"

    def matches(self, dt):
        wd = WEEKDAYS[self.weekday](self.n)
        d = dt.date()
        if self.period == "month":
            anchor = d.replace(day=1) if self.n > 0 else d + relativedelta(day=31)
        else:
            anchor = (
                d.replace(month=1, day=1) if self.n > 0 else d.replace(month=12, day=31)
            )
        return d == anchor + relativedelta(weekday=wd)


@dataclass
class TimeRange(Condition):
    start: time
    end: time

    def matches(self, dt):
        t = dt.time()
        if self.start <= self.end:
            return self.start <= t <= self.end
        return t >= self.start or t <= self.end


@dataclass
class TimeCondition:
    valid_on: list[Condition] = field(default_factory=list)
    invalid_on: list[Condition] = field(default_factory=list)
    tz: ZoneInfo | None = None

    def check(self, dt: datetime | None = None) -> bool:
        """Checks if the current date and time are valid"""
        if dt is None:
            dt = datetime.now(self.tz)
        elif self.tz is not None:
            dt = dt.astimezone(self.tz) if dt.tzinfo else dt.replace(tzinfo=self.tz)

        if any(c.matches(dt) for c in self.invalid_on):
            return False
        if not self.valid_on:
            return True
        return any(c.matches(dt) for c in self.valid_on)


@dataclass
class TriggerCondition:
    field_name: str
    trigger: str | bool | re.Pattern
    exact_match: bool = False

    def check(self, message: Message) -> bool:
        """Checks if the filed matches the trigger"""
        value = getattr(message, self.field_name)

        if isinstance(self.trigger, bool):
            return bool(value) == self.trigger

        elif isinstance(self.trigger, str):
            if self.exact_match:
                return str(value) == self.trigger
            else:
                return self.trigger in str(value)

        elif isinstance(self.trigger, re.Pattern):
            return re.search(self.trigger, str(value))

    @staticmethod
    def text(trigger: str, exact_match: bool = False) -> "TriggerCondition":
        return TriggerCondition("text", str(trigger), exact_match)

    def to_str(self):
        if isinstance(self.trigger, re.Pattern):
            trig = self.trigger.pattern
        else:
            trig = self.trigger
        return f"{self.field_name} == {trig}"


CONDITIONS = TriggerCondition | TimeCondition


@dataclass
class MessageMedia:
    media: str
    chat_id: int
    message_id: int

    async def refresh(self, client):
        fresh = await client.get_messages(self.chat_id, ids=self.message_id)
        self.media = base64.b64encode(bytes(fresh.media)).decode()
        return self.get()

    def get(self) -> TypeMessageMedia:
        return BinaryReader(base64.b64decode(self.media)).tgread_object()


@dataclass
class MessageReaction:
    text: str = ""
    media: MessageMedia = None
    # rich_message: list # ну его начерт. без парсера рич оформление в текст обрабатывать это проклято
    reply_to: Literal["trigger", "trigger_reply"] | int | None = ( # if int or None is set - send_to_chat_id is required
        "trigger_reply"
    )
    send_to_chat_id: int = None

    async def send(self, trigger_message: Message):
        kwargs = {}
        if self.reply_to == "trigger":
            fun = trigger_message.reply
        elif self.reply_to == "trigger_reply":
            fun = trigger_message.respond
        else:
            fun = trigger_message.client.send_message
            kwargs = {
                "entity": self.send_to_chat_id or trigger_message.chat_id,
                "reply_to": self.reply_to,
            }

        media = None
        if self.media:
            media = self.media.get()

        try:
            await fun(self.text, file=media, **kwargs)
        except (FileReferenceExpiredError, FileReferenceInvalidError):
            await fun(
                self.text, file=self.media.refresh(trigger_message.client), **kwargs
            )


REACTIONS = MessageReaction


@dataclass
class GoTrigger:
    conditions: list[TriggerCondition]
    time_condition: TimeCondition | None = None
    reactions: list[REACTIONS]

    def run(self, message: Message):
        pass

    async def _react(self, message: Message):
        for reaction in self.reactions:
            try:
                await reaction.send(message)
            except Exception:
                logger.exception("Error while reacting to the trigger %s", [cond.to_str() for cond in self.conditions])

    def export(self):
        return

    @staticmethod
    def load(exported_dict: dict) -> "GoTrigger":
        pass


@loader.tds
class GoTriggerMod(loader.Module):
    strings = {"name": "GoTrigger"}

    async def client_ready(self):
        pass

    @loader.watcher()
    async def main_watcher(self, message: Message):
        pass

    async def _add_to_assets(
        self, media_pull: TypeMessageMedia | list[TypeMessageMedia]
    ):
        pass

    @loader.command(ru_doc="[имяТриггера/ничего] - меню триггеров")
    async def gotriggs(self, message: Message):
        """[triggerName/none] - triggers menu"""
        pass

    @loader.command(
        ru_doc="[имяТриггера] [номерДействия] - добавить сообщение из ответа в конец действия Триггера"
    )
    async def goadd(self, message: Message):
        """[triggerName] [actionNumber] - append the replied message to the trigger's action"""
        return
        if not (reply := await message.get_reply_message()):
            return await utils.answer(message, "Вынеответили :(")


__version__ = (0, 0, 1)
