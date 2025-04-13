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
        "name": "DevMode",
        "notExist": " module does not exist",
        "module": ""
    }
    strings_ru = {
        "notExist":" не существует",
        "module": "Модуль "
    }
    
    @loader.command(
    ru_doc="[Название модуля/Пусто] открыть меню."
    )
    async def inspect(self,message):
        """[module/`empty`] open menu."""
        args = utils.get_args_raw(message)
        if args:
            if not self.lookup(args):#self.allmodules.lookup(args):
                await utils.answer(message, self.strings("module")+args+self.strings("notExist"))
                return
            await self.setMenu(message,args)
        else:
            await self.setMenu(message)
    
    async def setMenu(self,message=None,module=None):
        alldb = list(self._db.items())
        if module:#set reply markup for the module
            raw_vars,db = await self.getRaw(module,alldb)
            filtered = await self.filter(raw_vars)
            await utils.answer(message, f"filtered: {filtered}\n\ndb: {db} ")
            
        else:#set reply markup for the list of modules
            await utils.answer(message, f"test: {41+1/(2**2)*2/(1*3*(1+1)+2)}")
            
    
    async def getRaw(self,module,alldb):
        module = self.lookup(module).name#дб регистрозависимая сосо
        return self.lookup(module), next((n for n in alldb if n[0] == module), None)
        
    async def filter(self,vars):
        def basicVar(val):
            return isinstance(val, (int, float, str, bool, list, dict, tuple, type(None)))
        def fromWhichLib(val):
            try:
                module = val.__class__.__module__
                return module
            except:
                return False
        hikkaLibs=(
            "builtins", 
            "asyncio", 
            "hikka", 
            "telethon"
        )
        hikka=[
            "allclients",
            "tg_id",
            "_tg_id",
            "allmodules",
            "inline",
            "translator",
            "client",
            "_client",
            "lookup",
            "get_prefix"
        ]
        module=[
            "strings",
            "hikka_meta_pic",
            "__origin__",
            "name",
            "__doc__",
            "__version__",
            "config"
        ]
        
        filtered = {
            "readableVars": {},
            "libVars": {},
            "func": {},
            "config": {},    
            "hikka": {},
            "hikka_func": {},
            "hikkaVars": {},
            "module": {},
            "module_func": {},
            "idkWhatIsThis": {},
            
        }
        for key,val in vars.__dict__.items():               
            if key == "config" and isinstance(val, dict):
                filtered["config"] = val
                continue
            if "db" in key and not isinstance(val, (str, int)):
                continue
            if callable(val):
                if key in hikka:
                    filtered["hikka_func"][key] = val
                    continue
                if key in module:
                    filtered["module_func"][key] = val
                    continue
                filtered["func"][key] = val
                continue
            from_lib = fromWhichLib(val)
            if from_lib:
                if not from_lib.startswith(hikkaLibs):
                    filtered["libVars"].setdefault(from_lib, {})[key] = val
                else:
                    filtered["hikkaVars"].setdefault(from_lib, {})[key] = val
                continue
            if key in hikka:
                filtered["hikka"][key] = val
                continue
            if key in module:
                filtered["module"][key] = val
                continue
            if basicVar(val):
                filtered["readableVars"][key] = val
            else:
                filtered["idkWhatIsThis"][key] = val
        for section in filtered:
            if isinstance(filtered[section], dict):
                filtered[section] = dict(sorted(filtered[section].items()))
        return filtered