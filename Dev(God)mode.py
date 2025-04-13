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


#                     ⚠️⚠️⚠️                    #
#                     
#  Генератор был взят и  адаптирован из модуля:  #
#      https://mods.xdesai.org/managedb.py       #
#              Разработчик: @xdesai              #
#                Спасибо большое!                #

#                     ⚠️⚠️⚠️                    #



##### Фильтр #####

def filter(vars):
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
        if key in hikka:
            filtered["hikka"][key] = val
            continue
        if key in module:
            filtered["module"][key] = val
            continue
        if basicVar(val):
            filtered["readableVars"][key] = val
            continue
        from_lib = fromWhichLib(val)
        if from_lib:
            if not from_lib.startswith(hikkaLibs):
                filtered["libVars"].setdefault(from_lib, {})[key] = val
            else:
                filtered["hikkaVars"].setdefault(from_lib, {})[key] = val
            continue
        filtered["idkWhatIsThis"][key] = val
    for section in filtered:
        if isinstance(filtered[section], dict):
            filtered[section] = dict(sorted(filtered[section].items()))
    return filtered
##### Фильтр #####


from .. import loader, utils
@loader.tds
class devmode(loader.Module):
    """Модуль для исследования, просмотра и изменения переменных(датабаза, переменные класса) других модулей"""
    strings = {
        "name": "DevMode",
        "notExist": "<emoji document_id=5210952531676504517>🚫</emoji> {args} module does not exist",
        "list_text": "List of modules",
        "close_btn": "🔻 Close"
    }
    strings_ru = {
        "notExist": "<emoji document_id=5210952531676504517>🚫</emoji> Модуль {args} не существует",
        "list_text": "Список модулец",
        "close_btn": "🔻 Закрыть"
    }
    
    @loader.command(
    ru_doc="[Название модуля/Пусто] открыть меню."
    )
    async def inspect(self,message):
        """[module/`empty`] open menu."""
        args = utils.get_args_raw(message)
        if args:
            if not self.lookup(args):
                await utils.answer(message, self.strings("notExist").format(args))
                return
            await self.setMenu(message,args)
        else:
            await self.setMenu(message)


    async def setMenu(self,message,module=None,page=0):
        alldb = list(self._db.items())
        if module:#set reply markup for the module
            raw_vars,db = await self.getRaw(module,alldb)
            filtered = filter(raw_vars)
            await utils.answer(message, f"filtered:\n {filtered}\n\ndb: {db} ")
            
        else:#set reply markup for the list of modules
            await utils.answer(message, self.strings("list_text"), reply_markup=self.generate_info_all_markup(page))
            
            
    ##### Генератор #####

    def generate_info_all_markup(self, page_num=0):
        """Generate markup for inline form with 3x3 grid and navigation buttons"""
        items = list(self._db.items())
        markup = [[]]
        items_per_page = 9
        num_pages = len(items) // items_per_page + (1 if len(items) % items_per_page != 0 else 0)

        page_items = items[page_num * items_per_page: (page_num + 1) * items_per_page]
        for item in page_items:
            if len(markup[-1]) == 3:
                markup.append([])
            markup[-1].append({
                'text': f'{item[0]}',
                'callback': self.setMenu,
                'args': (item, page_num,),
            })

        nav_markup = []
        if page_num > 0:
            nav_markup.extend([
            {
                'text': '⇤',
                'callback': self.change_page,
                'args': [0],
            },
            {
                'text': '←',
                'callback': self.change_page,
                'args': [page_num - 1],
            }])
        else:
            nav_markup.extend([
            {
                'text': ' ',
                'callback': self.change_page,
                'args': [page_num],
            },
            {
                'text': ' ',
                'callback': self.change_page,
                'args': [page_num],
            }])
        nav_markup.append(
            {
                'text': f'{page_num+1}/{num_pages}',
                'callback': self.change_page,
                'args': [page_num],
            }
        )
        if page_num < num_pages - 1:
            nav_markup.extend([{
                'text': '→',
                'callback': self.change_page,
                'args': [page_num + 1],
            },
            {
                'text': '⇥',
                'callback': self.change_page,
                'args': [num_pages - 1],
            }
            ]
            )
        else:
            nav_markup.extend([
            {
                'text': ' ',
                'callback': self.change_page,
                'args': [page_num],
            },
            {
                'text': ' ',
                'callback': self.change_page,
                'args': [page_num],
            }])

        if nav_markup:
            markup.append(nav_markup)

        markup.append([])
        markup[-1].append(
            {
                'text': self.strings("close_btn"),
                'action': 'close',
            }
        )

        return markup
        
    ##### Генератор #####
    
    async def change_page(self, call, page_num):
        """Change to the specified page"""
        await call.edit(self.strings("list_text"), reply_markup=self.generate_info_all_markup(page_num))
    
    
    async def getRaw(self,module,alldb):
        module = self.lookup(module).name#дб регистрозависимая сосо
        return self.lookup(module), next((n for n in alldb if n[0] == module), None)