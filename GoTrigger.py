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
from ..types import InlineCall

logger = logging.getLogger(__name__)

WEEKDAYS = (MO, TU, WE, TH, FR, SA, SU)
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

TRIGGER_NAME_RE = re.compile(r"^\w+$")
PAGE_SIZE = 5


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
    selectable: ClassVar[bool] = True
    _registry: ClassVar[dict[str, type["Exportable"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Exportable._registry[cls.__name__] = cls

    @classmethod
    def variants(cls) -> list[type["Exportable"]]:
        return [
            sub
            for sub in Exportable._registry.values()
            if issubclass(sub, cls) and not sub.__abstractmethods__ and sub.selectable
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


@dataclass
class ChatScope(Condition):
    display_name: ClassVar[str] = "active_chats"
    selectable: ClassVar[bool] = False

    whitelist: set[int] = field(default_factory=set)
    blacklist: set[int] = field(default_factory=set)

    @property
    def is_global(self) -> bool:
        return not self.whitelist

    def check(self, message: Message) -> bool:
        chat_id = utils.get_chat_id(message)
        if chat_id in self.blacklist:
            return False
        return chat_id in self.whitelist if self.whitelist else True

    def describe(self) -> str:
        where = (
            "anywhere"
            if self.is_global
            else "in " + ", ".join(str(c) for c in sorted(self.whitelist))
        )
        if self.blacklist:
            where += " except " + ", ".join(str(c) for c in sorted(self.blacklist))
        return where


class Reaction(Exportable):
    @abstractmethod
    async def send(self, trigger_message: Message): ...


@dataclass
class MessageMedia(Exportable):
    display_name: ClassVar[str] = "media"

    media: str
    type: str
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
        return f"{self.type} media from t.me/c/{self.chat_id}/{self.message_id}"

    @staticmethod
    def parse(message_with_media: Message):
        if message_with_media.media is not None:
            media, chat_id, message_id = (
                MessageMedia.encode(message_with_media.media),
                message_with_media.chat_id,
                message_with_media.id,
            )
            media_type = media.__class__.__name__.lstrip("MessageMedia")

            return MessageMedia(media, media_type, chat_id, message_id)

        return None


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

    @staticmethod
    def parse(
        message: Message,
        media_message: Message | None = None,
        reply_to: Literal["trigger", "trigger_reply"] | int | None = "trigger_reply",
        send_to_chat_id: int = None,
    ):
        """Parses the replied message"""
        text = message.text
        media = MessageMedia.parse(media_message)

        return MessageReaction(
            text=text, media=media, reply_to=reply_to, send_to_chat_id=send_to_chat_id
        )


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
    active_chats: ChatScope = field(default_factory=ChatScope)

    async def run(self, message: Message):
        if self._check(message):
            await self._react(message)

    def _check(self, message: Message) -> bool:
        if not self.active_chats.check(message):
            logger.debug(
                "[%s] Out of scope: %s", self.name, self.active_chats.describe()
            )
            return False

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
        parts = [cond.describe() for cond in self.conditions]
        if not self.active_chats.is_global or self.active_chats.blacklist:
            parts.append(self.active_chats.describe())
        return " & ".join(parts)

    def export(self) -> dict:
        return {
            "name": self.name,
            "conditions": [cond.to_dict() for cond in self.conditions],
            "reactions": [reaction.to_dict() for reaction in self.reactions],
            "active_chats": self.active_chats.to_dict(),
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
            active_chats=ChatScope.from_dict(
                exported_dict.get("active_chats") or ChatScope().to_dict()
            ),
        )


@loader.tds
class GoTriggerMod(loader.Module):
    strings = {
        "name": "GoTrigger",
        "menu_main": """<tg-emoji emoji-id=5875271289605722323>🍔</tg-emoji> <b>GoTrigger: Меню</b>

<tg-emoji emoji-id=5854776233950188167>🏷</tg-emoji> Текущие триггеры ({shown}/{count}, Страница {page}):
<blockquote>{triggers}</blockquote>

Выберите один для настройки
<tg-emoji emoji-id=5343843578638538809>🍓</tg-emoji><tg-emoji emoji-id=5343843578638538809>🍓</tg-emoji><tg-emoji emoji-id=5343843578638538809>🍓</tg-emoji><tg-emoji emoji-id=5343843578638538809>🍓</tg-emoji><tg-emoji emoji-id=5875008416132370818>🔽</tg-emoji><tg-emoji emoji-id=5875008416132370818>🔽</tg-emoji><tg-emoji emoji-id=5875008416132370818>🔽</tg-emoji>
""",
        "menu_trigger_line": "<tg-emoji emoji-id=5343544262367682803>🍓</tg-emoji>&gt; {name} - {cond_count} условия, {reac_count} реакций",
        "menu_trigger": """<tg-emoji emoji-id=5875271289605722323>🍔</tg-emoji> <b>GoTrigger: Настройка</b>

<tg-emoji emoji-id=5875019892284985369>➕</tg-emoji> Имя: {name}

<tg-emoji emoji-id=5960714428394507968>👁</tg-emoji> <b>Условия</b>:
{conditions}

<tg-emoji emoji-id=5884123981706956210>➡️</tg-emoji> <b>Порядок отправки</b>:
{reactions}
""",
        "menu_trigger_desc_line": "<tg-emoji emoji-id=5343544262367682803>😀</tg-emoji>&gt; {desc}",
        "menu_trigger_no_conditions": "<tg-emoji emoji-id=5343544262367682803>😀</tg-emoji>&gt; отсутствуют",
        "menu_trigger_no_reactions": "<tg-emoji emoji-id=5343544262367682803>😀</tg-emoji>&gt; отсутствуют",
        "btn_rename": "Изменить имя",
        "btn_conditions": "Условия",
        "btn_reactions": "Реакции",
        "back": "Назад",
        "close": "Закрыть",
        "trigger_not_found": "Триггер <code>{name}</code> не найден",
        "rename_prompt": "Введите новое имя триггера (без пробелов)",
        "rename_invalid": "Имя триггера не должно содержать пробелов и других разделителей. Разрешены только буквы, цифры и <code>_</code>",
        "rename_exists": "Триггер с именем <code>{name}</code> уже существует",
        "rename_success": "Имя триггера изменено на <code>{name}</code>",
        "goadd_no_name": "Вы не указали имя триггера",
        "goadd_no_reply": "Вынеответили :(",
        "goadd_empty": "Нечего добавлять в триггер (нет ни текста, ни медиа)",
        "goadd_trigger_not_found": "Триггера с именем <code>{name}</code> не существует. Невозможно добавить сообщение",
        "goadd_success": "Действие успешно добавлено в триггер!",
    }

    def __init__(self):
        """"""
        # self.config = loader.ModuleConfig(
        #     loader.ConfigCategory(
        #         "defaults",
        #         loader.ConfigValue(
        #         ),
        #         doc=lambda: self.strings["_cfg_defaults"],
        #     )
        # )

    async def client_ready(self):
        saved_triggers: list[dict] = self.get("triggers", [])

        self.triggers = [GoTrigger.load(trig) for trig in saved_triggers]

        heroku_forum = self._db.get("heroku.forums", "channel_id", 0)
        self.assets_topic = await utils.asset_forum_topic(
            self.client,
            self.db,
            heroku_forum,
            "GoTrigger Assets",
            self.strings["_assets_topic"],
        )

    @loader.watcher()
    async def main_watcher(self, message: Message):
        if not self.triggers:
            return

        # scheduled_tasks = []

        for trigger in self.triggers:
            if task := await trigger.run(message):
                pass
                # scheduled_tasks.extend(task)

    def _save_triggers(self):
        self.set("triggers", [trigger.export() for trigger in self.triggers])

    async def _add_to_assets(
        self,
        media: TypeMessageMedia,
    ) -> Message:
        heroku_forum = self._db.get("heroku.forums", "channel_id", 0)

        return await self.client.send_message(
            heroku_forum, file=media, reply_to=self.assets_topic.id
        )

    async def _trigger_menu(self, call: InlineCall, name: str, page: int = 0):
        trigger = next((t for t in self.triggers if t.name == name), None)
        if trigger is None:
            return await call.answer(
                self.strings["trigger_not_found"].format(name=name), show_alert=True
            )

        conditions = "\n".join(
            self.strings["menu_trigger_desc_line"].format(
                desc=utils.escape_html(cond.describe()[:20])
            )
            for cond in trigger.conditions
        ) or self.strings["menu_trigger_no_conditions"]

        reactions = "\n".join(
            self.strings["menu_trigger_desc_line"].format(
                desc=utils.escape_html(reaction.describe()[:20])
            )
            for reaction in trigger.reactions
        ) or self.strings["menu_trigger_no_reactions"]

        await utils.answer(
            call,
            self.strings["menu_trigger"].format(
                name=trigger.name,
                conditions=conditions,
                reactions=reactions,
            ),
            reply_markup=self._build_trigger_markup(trigger, page),
        )

    def _build_trigger_markup(self, trigger: GoTrigger, page: int = 0):
        return [
            [
                {
                    "text": self.strings["btn_rename"],
                    "input": self.strings["rename_prompt"],
                    "handler": self._trigger_rename_handler,
                    "args": (trigger.name,),
                    "kwargs": {"page": page},
                },
            ],
            [
                {
                    "text": self.strings["btn_conditions"],
                    "callback": self._inl_trigger_conditions,
                    "kwargs": {"name": trigger.name, "page": page},
                },
            ],
            [
                {
                    "text": self.strings["btn_reactions"],
                    "callback": self._inl_trigger_reactions,
                    "kwargs": {"name": trigger.name, "page": page},
                },
            ],
            [
                {
                    "text": self.strings["back"],
                    "callback": self._menu,
                    "kwargs": {"page": page},
                },
                {"text": self.strings["close"], "action": "close"},
            ],
        ]

    async def _trigger_rename_handler(
        self, call: InlineCall, data: str, name: str, page: int = 0
    ):
        trigger = next((t for t in self.triggers if t.name == name), None)
        if trigger is None:
            return await call.answer(
                self.strings["trigger_not_found"].format(name=name), show_alert=True
            )

        new_name = data.strip()
        if not TRIGGER_NAME_RE.fullmatch(new_name):
            return await call.answer(self.strings["rename_invalid"], show_alert=True)

        if new_name != trigger.name and any(
            t.name == new_name for t in self.triggers
        ):
            return await call.answer(
                self.strings["rename_exists"].format(name=new_name), show_alert=True
            )

        trigger.name = new_name
        self._save_triggers()

        await call.answer(self.strings["rename_success"].format(name=new_name))
        await self._trigger_menu(call, new_name, page)

    async def _inl_trigger_conditions(self, call: InlineCall, name: str, page: int = 0):
        pass

    async def _inl_trigger_reactions(self, call: InlineCall, name: str, page: int = 0):
        pass

    async def _inl_add_trigger(self, call: InlineCall, data: dict = None):
        return

    def _build_main_markup(self, triggers: list[GoTrigger], page: int = 0):
        buttons = []
        for trigger in triggers:
            buttons.append(
                [
                    {
                        "text": trigger.name,
                        "callback": self._trigger_menu,
                        "kwargs": {"name": trigger.name, "page": page},
                    }
                ]
            )

        nav_row = []
        if page > 0:
            nav_row.append(
                {
                    "text": "⬅️",
                    "callback": self._menu,
                    "kwargs": {"page": page - 1},
                }
            )
        if (page + 1) * PAGE_SIZE < len(self.triggers):
            nav_row.append(
                {
                    "text": "➡️",
                    "callback": self._menu,
                    "kwargs": {"page": page + 1},
                }
            )
        if nav_row:
            buttons.append(nav_row)

        buttons.append(
            [
                {
                    "text": self.strings["btn_add_trigger"],
                    "callback": self._inl_add_trigger,
                },
            ]
        )
        buttons.append(
            [
                {
                    "text": self.strings["close"],
                    "action": "close",
                },
            ]
        )
        return buttons

    async def _menu(self, message: Message, page: int = 0):
        text = self.strings["menu_main"]

        page_triggers = self.triggers[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

        triggs = "\n".join(
            [
                self.strings["menu_trigger_line"].format(
                    name=trigger.name,
                    cond_count=len(trigger.conditions),
                    reac_count=len(trigger.reactions),
                )
                for trigger in page_triggers
            ]
        )

        reply_markup = self._build_main_markup(page_triggers, page)

        await utils.answer(
            message,
            text.format(
                shown=len(page_triggers),
                count=len(self.triggers),
                page=page,
                triggers=triggs,
            ),
            reply_markup=reply_markup,
        )

    @loader.command(ru_doc="[имяТриггера/ничего] - меню триггеров")
    async def gotriggs(self, message: Message):
        """[triggerName/none] - triggers menu"""
        await self._menu(message)

    @loader.command(
        ru_doc="[имяТриггера] - добавить сообщение из ответа в конец действия Триггера"
    )
    async def goadd(self, message: Message):
        """[triggerName] - append the replied message to the trigger's action"""
        if not (args := utils.get_args(message)):
            return await utils.answer(message, self.strings["goadd_no_name"])

        trigger_name = args[0]

        if not (reply := await message.get_reply_message()):
            return await utils.answer(message, self.strings["goadd_no_reply"])
        if not (message.text or message.media):
            return await utils.answer(message, self.strings["goadd_empty"])

        try:
            trigger = next(
                trigger
                for trigger in self.triggers
                if trigger.name.lower() in trigger_name
            )
        except StopIteration:
            return await utils.answer(
                message,
                self.strings["goadd_trigger_not_found"].format(name=trigger_name),
            )

        if reply.media:
            media_message = await self._add_to_assets(reply.media)

        reaction = MessageReaction.parse(
            message=reply,
            media_message=media_message,
        )

        trigger.reactions.append(reaction)

        await utils.answer(message, self.strings["goadd_success"])


__version__ = (0, 0, 67)
