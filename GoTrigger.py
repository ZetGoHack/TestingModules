# ░░░███░███░███░███░███
# ░░░░░█░█░░░░█░░█░░░█░█
# ░░░░█░░███░░█░░█░█░█░█
# ░░░█░░░█░░░░█░░█░█░█░█
# ░░░███░███░░█░░███░███

# meta developer: @ZetGo

import logging

from herokutl.tl.types import TypeMessageMedia
from herokutl.tl.custom import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


class GoTrigger:
    def __init__(self):
        pass

    def _react(self):
        pass

    def export(self):
        return

    @staticmethod
    def load(exported_dict: dict) -> "GoTrigger":
        for classname in exported_dict.get("classnames", []):
            try:
                classname: str = classname
            except ImportError:
                logger.exception(
                    "%s Can't load %s trigger because of exception",
                    utils.ascii_face(),
                    exported_dict["name"],
                )


class GoTriggerMod(loader.Module):
    strings = {"name": "GoTrigger"}

    async def client_ready(self):
        pass

    @loader.watcher()
    async def main_watcher(self, message: Message):
        pass

    async def _add_to_assets(self, media_pull: TypeMessageMedia | list[TypeMessageMedia]):
        pass

    @loader.command(ru_doc="[имяТриггера/ничего] - меню триггеров")
    async def gotriggs(self, message: Message):
        """[triggerName/none] - triggers menu"""
        pass

    @loader.command(ru_doc="[имяТриггера] [номерДействия] - добавить сообщение из ответа в конец действия Триггера")
    async def goadd(self, message: Message):
        """[triggerName] [actionNumber] - append the replied message to the trigger's action"""
        return
        if not (reply := await message.get_reply_message()):
            return await utils.answer(message, "Вынеответили :(")

__version__ = (0, 0, 0)
