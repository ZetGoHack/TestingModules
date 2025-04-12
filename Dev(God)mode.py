#░░░░░░░░░░░░░░░░░░░░░░
#░░░░░░░░░░ █░░██░░░░░░
#░░░░░░░░░██.█████░░░░░
#░░░░░░░░░███ ████░░░░░
#░░░░░░░░░░███ ██░░░░░░
#░░░░░░░░░░░░██ ░░░░░░░
#░░░░░░░░░░░░░░░░░░░░░░
#░░░░░░░░░█▔█░░█░█░░░░░
#░░░░░░░░░██░░░░█░░░░░░
#░░░░░░░░░█▁█░░░█░░░░░░
#░░░░░░░░░░░░░░░░░░░░░░
#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]


# meta developer: @nullmod
from .. import loader, utils
@loader.tds
class devmode(loader.Module):
    """Модуль для исследования, просмотра и изменения переменных(датабаза, переменные класса) других модулей"""
    strings = {
        "name": "Dev(god)mode",
        "notExist": " module is not exist."
    }
    strings_ru = {
        "notExist":" не существует."
    }
    
    @loader.command(
    ru_doc="[Название модуля/Пусто] открыть меню."
    )
    async def inspect(self,m):
        """[module/`empty`] open menu."""
        args = utils.get_args_raw(m)
        if args:
            if not self.lookup(args):#self.allmodules.lookup(args):
                await m.edit(args+self.strings("notExist"))
                return
            await self.setMenu(m,args)
        else:
            await self.setMenu(m)
    
    async def setMenu(self,m=None,module=None):
        if module:
            db = self.lookup(module)._db.items#allmodules.lookup(args)._db.items
            raw_vars = None
            await m.edit(f"db: {db}")
        else:
            await m.edit(f"test: {41+1}")
