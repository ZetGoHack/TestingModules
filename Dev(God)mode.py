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
        "notExist": " module does not exist"
    }
    strings_ru = {
        "notExist":" не существует"
    }
    
    @loader.command(
    ru_doc="[Название модуля/Пусто] открыть меню"
    )
    async def inspect(self,message):
        """[module/`empty`] open menu."""
        args = utils.get_args_raw(message)
        if args:
            if not self.lookup(args):#self.allmodules.lookup(args):
                await message.edit("<emoji document_id=5210952531676504517>🚫</emoji> "+args+self.strings("notExist"))
                return
            await self.setMenu(message,args)
        else:
            await self.setMenu(message)
    
    async def setMenu(self,message=None,module=None):
        if module:#set reply markup for module
            raw_vars,db = await self.getRaw(module,alldb)
            filtered = await self.filter(raw_vars)
            await m.edit(f"filtered: {filtered}\n\ndb: {bd}")
            
        else:#set reply markup for list of modules
            await m.edit(f"test: {41+1}")
            
    
    async def getRaw(self,module,alldb):
        module = self.lookup(module).name#дб регистрозависимая сосо
        return dir(self.lookup(module)), next((n for n in alldb if n[0] == module), None)
        
    async def filter(self,vars):
        filtered = {
            "readableVars": {},
            "externalVars": {},
            "func": {},
            "config": {},
            "hikka": {},
        }
        for key,val in data.items():
            if key == "config" and isinstance(val, dict):
                result["config"] = val
                continue
            if "db" in key and not isinstance(val, (str, int)):
                continue
            if callable(val):
                filtered["functions"][key] = val
                continue
            if basicVar(val):
                filtered["readableVars"][key] = val
            else:
                filtered["externalVars"][key] = val
        return filtered