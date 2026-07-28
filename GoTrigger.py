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
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, time
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from typing import ClassVar, Literal
from zoneinfo import ZoneInfo

from herokutl.extensions import BinaryReader
from herokutl.errors import FileReferenceExpiredError, FileReferenceInvalidError
from herokutl.tl.types import TypeMessageMedia
from herokutl.tl.custom import Message

from .. import loader, utils

logger = logging.getLogger(__name__)

WEEKDAYS = (MO, TU, WE, TH, FR, SA, SU)
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _encode(value):
    if isinstance(value, Exportable):
        return value.to_dict()
    if isinstance(value, (set, frozenset)):
        return {"__set__": [_encode(v) for v in sorted(value)]}
    if isinstance(value, (list, tuple)):
        return [_encode(v) for v in value]
    if isinstance(value, time):
        return {"__time__": value.isoformat()}
    if isinstance(value, re.Pattern):
        return {"__re__": value.pattern, "flags": value.flags}
    if isinstance(value, ZoneInfo):
        return {"__tz__": str(value)}
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise TypeError("Only str keys can be exported")
        return {"__dict__": {k: _encode(v) for k, v in value.items()}}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(f"Don't know how to export {type(value).__name__}")


def _decode(value):
    if isinstance(value, list):
        return [_decode(v) for v in value]
    if isinstance(value, dict):
        if "__dict__" in value:
            return {k: _decode(v) for k, v in value["__dict__"].items()}
        if "__set__" in value:
            return {_decode(v) for v in value["__set__"]}
        if "__time__" in value:
            return time.fromisoformat(value["__time__"])
        if "__re__" in value:
            return re.compile(value["__re__"], value.get("flags", 0))
        if "__tz__" in value:
            return ZoneInfo(value["__tz__"])
        if "type" in value:
            return Exportable.from_dict(value)
        raise ValueError(f"Unrecognized payload: {value}")
    return value


class Exportable(ABC):
    display_name: ClassVar[str] = ""
    _registry: ClassVar[dict[str, type["Exportable"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Exportable._registry[cls.__name__] = cls

    @classmethod
    def variants(cls) -> list[type["Exportable"]]:
        return [
            sub
            for sub in Exportable._registry.values()
            if issubclass(sub, cls) and not sub.__abstractmethods__
        ]

    @abstractmethod
    def describe(self) -> str: ...

    def to_dict(self) -> dict:
        return {
            "type": type(self).__name__,
            **{f.name: _encode(getattr(self, f.name)) for f in fields(self)},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Exportable":
        target = Exportable._registry.get(data["type"])
        if target is None:
            raise ValueError(f"Unknown type: {data['type']}")
        if not issubclass(target, cls) or target.__abstractmethods__:
            raise ValueError(f"{data['type']} is not a usable {cls.__name__}")
        return target._from_payload(
            {k: _decode(v) for k, v in data.items() if k != "type"}
        )

    @classmethod
    def _from_payload(cls, payload: dict) -> "Exportable":
        return cls(**payload)


class TimeMatchRule(Exportable):
    @abstractmethod
    def matches(self, dt: datetime) -> bool: ...


class Condition(Exportable):
    @abstractmethod
    def check(self, message: Message) -> bool: ...


@dataclass
class AllOf(TimeMatchRule):
    display_name: ClassVar[str] = "all_of"

    conditions: list[TimeMatchRule] = field(default_factory=list)

    @staticmethod
    def of(*conditions: TimeMatchRule) -> "AllOf":
        return AllOf(list(conditions))

    def matches(self, dt: datetime) -> bool:
        return all(c.matches(dt) for c in self.conditions)

    def describe(self) -> str:
        return " & ".join(c.describe() for c in self.conditions)


@dataclass
class Weekday(TimeMatchRule):
    display_name: ClassVar[str] = "day_of_week"

    days: set[int]

    def matches(self, dt):
        return dt.weekday() in self.days

    def describe(self) -> str:
        return ", ".join(WEEKDAY_NAMES[d] for d in sorted(self.days))


@dataclass
class DayOfMonth(TimeMatchRule):
    display_name: ClassVar[str] = "day_of_month"

    days: set[int]

    def matches(self, dt):
        return dt.day in self.days

    def describe(self) -> str:
        return "day " + ", ".join(str(d) for d in sorted(self.days))


@dataclass
class LastDayOfMonth(TimeMatchRule):
    display_name: ClassVar[str] = "last_day_of_month"

    def matches(self, dt):
        return dt.day == (dt + relativedelta(day=31)).day

    def describe(self) -> str:
        return "last day of month"


@dataclass
class NthWeekday(TimeMatchRule):
    display_name: ClassVar[str] = "nth_day_of_week"

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

    def describe(self) -> str:
        if self.n == -1:
            nth = "last"
        else:
            nth = f"#{abs(self.n)}" + (" from the end" if self.n < 0 else "")
        return f"{nth} {WEEKDAY_NAMES[self.weekday]} of {self.period}"


@dataclass
class TimeRange(TimeMatchRule):
    display_name: ClassVar[str] = "time_range"

    start: time
    end: time

    def matches(self, dt):
        t = dt.time()
        if self.start <= self.end:
            return self.start <= t <= self.end
        return t >= self.start or t <= self.end

    def describe(self) -> str:
        return f"{self.start:%H:%M}-{self.end:%H:%M}"


@dataclass
class TimeCondition(Condition):
    display_name: ClassVar[str] = "date_and_time"

    valid_on: list[TimeMatchRule] = field(default_factory=list)
    invalid_on: list[TimeMatchRule] = field(default_factory=list)
    tz: ZoneInfo | None = None

    def check(self, message: Message) -> bool:
        return self.matches_at(self.instant(message))

    def instant(self, message: Message | None = None) -> datetime:
        dt: datetime | None = getattr(message, "date", None)
        if dt is None:
            return datetime.now(self.tz)
        return dt.astimezone(self.tz) if dt.tzinfo else dt.replace(tzinfo=self.tz)

    def matches_at(self, dt: datetime) -> bool:
        if any(c.matches(dt) for c in self.invalid_on):
            return False
        if not self.valid_on:
            return True
        return any(c.matches(dt) for c in self.valid_on)

    def describe(self) -> str:
        parts = []
        if self.valid_on:
            parts.append("on " + " / ".join(c.describe() for c in self.valid_on))
        if self.invalid_on:
            parts.append("except " + " / ".join(c.describe() for c in self.invalid_on))
        if self.tz:
            parts.append(f"({self.tz})")
        return " ".join(parts) or "always"


@dataclass
class TriggerCondition(Condition):
    display_name: ClassVar[str] = "message_field"

    field_name: str
    trigger: str | bool | re.Pattern
    exact_match: bool = False

    def check(self, message: Message) -> bool:
        """Checks if the field matches the trigger"""
        value = getattr(message, self.field_name, None)

        if isinstance(self.trigger, bool):
            return bool(value) == self.trigger

        elif isinstance(self.trigger, str):
            if self.exact_match:
                return str(value) == self.trigger
            else:
                return self.trigger in str(value)

        elif isinstance(self.trigger, re.Pattern):
            return bool(self.trigger.search(str(value)))

        return False

    @staticmethod
    def text(trigger: str, exact_match: bool = False) -> "TriggerCondition":
        return TriggerCondition("text", str(trigger), exact_match)

    def describe(self) -> str:
        if isinstance(self.trigger, re.Pattern):
            return f"{self.field_name} ~ {self.trigger.pattern}"
        if isinstance(self.trigger, bool):
            return f"{self.field_name} is {self.trigger}"
        return f"{'' if self.exact_match else 'in '}{self.field_name}: {self.trigger}"


class Reaction(Exportable):
    @abstractmethod
    async def send(self, trigger_message: Message): ...


@dataclass
class MessageMedia(Exportable):
    display_name: ClassVar[str] = "media"

    media: str
    chat_id: int
    message_id: int

    async def refresh(self, client):
        fresh = await client.get_messages(self.chat_id, ids=self.message_id)
        self.media = base64.b64encode(bytes(fresh.media)).decode()
        return self.get()

    def get(self) -> TypeMessageMedia:
        return BinaryReader(base64.b64decode(self.media)).tgread_object()

    def describe(self) -> str:
        return f"media from {self.chat_id}/{self.message_id}"


@dataclass
class MessageReaction(Reaction):
    display_name: ClassVar[str] = "send_message"

    text: str = ""
    media: MessageMedia | None = None
    # rich_message: list # ну его начерт. без парсера рич оформление в текст обрабатывать это проклято
    reply_to: Literal["trigger", "trigger_reply"] | int | None = (
        "trigger_reply"  # if int or None is set - send_to_chat_id is required
    )
    send_to_chat_id: int | None = None

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
                self.text,
                file=await self.media.refresh(trigger_message.client),
                **kwargs,
            )

    def describe(self) -> str:
        preview = utils.escape_html(self.text[:40]) or (
            self.media.describe() if self.media else "empty"
        )
        return f"send {preview} -> {self.reply_to}"


def _validate_registry():
    for name, sub in Exportable._registry.items():
        if sub.__abstractmethods__:
            continue
        if not is_dataclass(sub):
            raise TypeError(f"{name} must be a @dataclass to be exportable")
        if not sub.display_name:
            raise TypeError(f"{name} must set display_name")


_validate_registry()


@dataclass
class GoTrigger:
    name: str
    conditions: list[Condition]
    reactions: list[Reaction]

    async def run(self, message: Message):
        if self._check(message):
            await self._react(message)

    def _check(self, message: Message) -> bool:
        logger.debug(
            "[%s] Started checking with %s conditions", self.name, len(self.conditions)
        )
        for condition in self.conditions:
            if not condition.check(message):
                logger.debug("[%s] No match on %s", self.name, condition.describe())
                return False

        logger.debug("[%s] Match", self.name)
        return True

    async def _react(self, message: Message):
        for reaction in self.reactions:
            try:
                await reaction.send(message)
            except Exception:
                logger.exception(
                    "Error while reacting to the trigger %s: %s",
                    self.name,
                    self.describe(),
                )

    def describe(self) -> str:
        return " & ".join(cond.describe() for cond in self.conditions)

    def export(self) -> dict:
        return {
            "name": self.name,
            "conditions": [cond.to_dict() for cond in self.conditions],
            "reactions": [reaction.to_dict() for reaction in self.reactions],
        }

    @classmethod
    def load(cls, exported_dict: dict) -> "GoTrigger":
        return cls(
            name=exported_dict["name"],
            conditions=[
                Condition.from_dict(cond) for cond in exported_dict["conditions"]
            ],
            reactions=[
                Reaction.from_dict(reaction) for reaction in exported_dict["reactions"]
            ],
        )


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


__version__ = (0, 0, 3)
