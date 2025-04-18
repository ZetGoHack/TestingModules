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

def _filter(vars):
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
    if not vars:
        return None
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
import html, io
@loader.tds
class devmode(loader.Module):
    """Модуль для исследования, просмотра и изменения переменных(датабаза, переменные класса) других модулей"""
    strings = {
        "name": "DevMode",
        "notExist": "<emoji document_id=5210952531676504517>🚫</emoji> {args} module does not exist",
        "list_text": "List of modules",
        "vars_text": "[{module}] List of variables",
        "db_text": "[{module}] DataBase",
        "back": "◀ Back",
        "close_btn": "🔻 Close"
    }
    strings_ru = {
        "notExist": "<emoji document_id=5210952531676504517>🚫</emoji> Модуль {args} не существует",
        "list_text": "Список модулей",
        "vars_text": "[{module}] Список содержимого",
        "db_text": "[{module}] Датабаза",
        "back": "◀ Назад",
        "close_btn": "🔻 Закрыть"
    }
    
    @loader.command(
    ru_doc="[Название модуля/Пусто] открыть меню."
    )
    async def inspect(self,message,args=None,page=0):
        """[module/`empty`] open menu."""
        arg = args if args else utils.get_args_raw(message)
        if arg:
            if not self.lookup(arg) and not next((n for n in list(self._db.items()) if n[0] == arg), None):
                await utils.answer(message, self.strings("notExist").format(args=arg),reply_markup={"text":f"{self.strings('back')}","callback": self.setMenu, "args": (None,page,)})
                return
            await self.setMenu(message,arg,page)
        else:
            await self.setMenu(message)


    async def setMenu(self,message,module=None,page=0):
        alldb = list(self._db.items())
        if module:#set reply markup for the module
            lookup = self.lookup(module)
            raw_vars, db = (
                lookup if lookup else None,next((n for n in alldb if n[0].lower() == module.lower()), None)
            )
            filtered = _filter(raw_vars)
            await utils.answer(message, f"{module}",reply_markup=[
                    [
                        {"text":"📄 Module vars","callback":self.showVars, "args": (module,)},
                        {"text":"📁 DB","callback":self.showDB, "args": (module,)}
                    ],
                    [
                        {"text":f"{self.strings('back')}","callback": self.setMenu,"args":(None,page,)
                        }
                    ]
                ]
            ) #<pre><code class='language-{module}'>{html.escape(str(filtered))}</code></pre>\n\n<pre><code class='language-db'>{html.escape(str(db))}</code></pre>
           
        else:#set reply markup for the list of modules
            await utils.answer(message, self.strings("list_text"), reply_markup=self.generate_info_all_markup(page))
            
    async def showVars(self,call,module):
        mode = 2
        await call.edit(self.strings("vars_text").format(module=module), reply_markup="")
        
    async def showDB(self,call,module):
        mode = 3
        await call.edit(self.strings("db_text").format(module=module), reply_markup="")
            
    ##### Генератор #####

    def generate_info_all_markup(self,page_num=0):
        """Generate markup for inline form with 3x3 grid and navigation buttons"""
        items = list(self._db.items())
        markup = [[]]
        items_per_page = 3*4
        num_pages = len(items) // items_per_page + (1 if len(items) % items_per_page != 0 else 0)

        page_items = items[page_num * items_per_page: (page_num + 1) * items_per_page]
        for item in page_items:
            if len(markup[-1]) == 3:
                markup.append([])
            markup[-1].append({
                'text': f'{item[0]}' if self.lookup(item[0]) else f'[{item[0]}]',
                'callback': self.inspect,
                'args': (item[0],page_num),
            })

        nav_markup = []
        if page_num > 0:
            nav_markup.extend([
            {
                'text': '⇤' if page_num != 1 else ' ',
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
                'text': '⇥' if page_num != num_pages -2 else ' ',
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
    
    async def change_page(self, call, page_num, mode=0):
        """Change to the specified page"""
        if mode == 0:
            await call.edit(self.strings("list_text"), reply_markup=self.generate_info_all_markup(page_num))
        if mode == 1:
            pass
        if mode == 2:
            await call.edit(self.strings("vars_text").format(module=module), reply_markup=self.generate_info_all_markup(mode,list(self.lookup(module).__dict__.items()),3,4,page_num))
        if mode == 3:
            await call.edit(self.strings("db_text").format(module=module), reply_markup=self.generate_info_all_markup(mode,next((n[1] for n in list(self._db.items()) if n[0].lower() == module.lower()), None),3,4,page_num))