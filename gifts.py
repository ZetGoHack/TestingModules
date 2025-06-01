#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]

# meta developer: @nullmod
# scope: heroku_min 1.7.0
# scope: hikka_min 1.7.0

# -      main      - #
from .. import loader, utils
# -      func      - #
from telethon.tl.functions.payments import GetSavedStarGiftsRequest
# -       --       - #

@loader.tds
class Gifts(loader.Module):
    """Just a module for working with gifts"""
    strings = {
        "name": "Gifts",
        "toomany": "Too many arguments",
        "": "",
        "": "",
    }
    strings_ru = {
        "toomany": "Слишком много аргументов"
    }

    @loader.command(ru_doc="[юзернейм/ответ/'me'] посмотреть подарки пользователя")
    async def gifts(self, message):
        """[username/reply/'me'] view user's gifts"""
        args = utils.get_args_raw(message).split()
        if len(args) > 1:
            await utils.answer(message, self.strings["toomany"])
            return
        if len(args):
            username = args[0]
            user_gifts = await self._get_gifts(username)

    async def _get_gifts(self, username):
        return None