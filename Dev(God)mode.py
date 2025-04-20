# ░░░░░░░░░░░░░░░░░░░░░░
# ░░░░░░░░░░ █░░██░░░░░░
# ░░░░░░░░░██.█████░░░░░
# ░░░░░░░░░███ ████░░░░░
# ░░░░░░░░░░███ ██░░░░░░
# ░░░░░░░░░░░░██ ░░░░░░░
# ░░░░░░░░░░░░░░░░░░░░░░
# ░░░░░░░░░█▔█░░█░█░░░░░
# ░░░░░░░░░██░░░░█░░░░░░
# ░░░░░░░░░█▁█░░░█░░░░░░
# ░░░░░░░░░░░░░░░░░░░░░░
# ░░░███░███░███░███░███
# ░░░░░█░█░░░░█░░█░░░█░█
# ░░░░█░░███░░█░░█░█░█░█
# ░░░█░░░█░░░░█░░█░█░█░█
# ░░░███░███░░█░░███░███
# H:Mods Team [💎]


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

    hikkaLibs = ("builtins", "asyncio", "hikka", "telethon")
    hikka = [
        "allclients",
        "tg_id",
        "_tg_id",
        "allmodules",
        "inline",
        "translator",
        "client",
        "_client",
        "lookup",
        "get_prefix",
    ]
    module = [
        "strings",
        "hikka_meta_pic",
        "__origin__",
        "name",
        "__doc__",
        "__version__",
        "config",
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
    for key, val in vars.__dict__.items():
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
import html, ast


@loader.tds
class devmode(loader.Module):
    """Модуль для исследования, просмотра и изменения переменных(датабаза, переменные класса) других модулей"""

    strings = {
        "name": "DevMode",
        "notExist": "<emoji document_id=5210952531676504517>🚫</emoji> {args} module does not exist",
        "list_text": "List of modules",
        "vars_text": "[{module}] List of variables",
        "db_text": "[{module}] DataBase",
        "notWaiting": "<emoji document_id=5210952531676504517>🚫</emoji> Nothing is waiting for a value to edit.\n\n{input}",
        "waiting": "Waiting for a value to edit...\n<code>.editvar [value]</code>",
        "nothingEntered": "<emoji document_id=5210952531676504517>🚫</emoji> Nothing entered",
        "back": "◀ Back",
        "close_btn": "🔻 Close",
    }
    strings_ru = {
        "notExist": "<emoji document_id=5210952531676504517>🚫</emoji> Модуль {args} не существует",
        "list_text": "Список модулей",
        "vars_text": "[{module}] Список содержимого",
        "db_text": "[{module}] Датабаза",
        "notWaiting": "<emoji document_id=5210952531676504517>🚫</emoji> Ничего не ожидает значения для редактирования.\n\n{input}",
        "waiting": "Ожидание значения для редактирования...\n<code>.editvar [значение]</code>",
        "nothingEntered": "<emoji document_id=5210952531676504517>🚫</emoji> Ничего не введено",
        "back": "◀ Назад",
        "close_btn": "🔻 Закрыть",
    }

    async def client_ready(self):
        self.handle = None

    @loader.command(ru_doc="[Название модуля/Пусто] открыть меню.")
    async def inspect(self, message, args=None, page=0):
        """[module/`empty`] open menu."""
        arg = args if args else utils.get_args_raw(message)
        if arg:
            if not self.lookup(arg) and not next(
                (n for n in list(self._db.items()) if n[0] == arg), None
            ):
                await utils.answer(
                    message,
                    self.strings("notExist").format(args=arg),
                    reply_markup={
                        "text": f"{self.strings('back')}",
                        "callback": self.setMenu,
                        "args": (
                            None,
                            page,
                        ),
                    },
                )
                return
            await self.setMenu(message, arg, page)
        else:
            await self.setMenu(message)

    @loader.command(ru_doc="Изменить значение")
    async def editVar(self, message):
        """Change var value"""
        input = utils.get_args_raw(message)
        if not self.handle:
            await message.edit(f"{self.strings('notWaiting').format(input=input)}")
            return
        if not input:
            await message.edit(self.strings("nothingEntered"))
            return
        await message.delete()
        await self.handle[0](input)


    async def setMenu(self, message, module=None, page=0):
        alldb = list(self._db.items())
        if module:
            lookup = self.lookup(module)
            raw_vars, db = (
                lookup if lookup else None,
                next((n for n in alldb if n[0].lower() == module.lower()), None),
            )
            self.filtered = _filter(raw_vars)
            await utils.answer(
                message,
                f"{module}",
                reply_markup=[
                    [
                        {
                            "text": "📄 Module vars",
                            "callback": self.filteredVars,
                            "args": (module, page,),
                        },
                        {"text": "📁 DB", "callback": self.showDB, "args": (module,)},
                    ],
                    [
                        {
                            "text": f"{self.strings('back')}",
                            "callback": self.setMenu,
                            "args": (
                                None,
                                page,
                            ),
                        }
                    ],
                ],
            )  # <pre><code class='language-{module}'>{html.escape(str(filtered))}</code></pre>\n\n<pre><code class='language-db'>{html.escape(str(db))}</code></pre>

        else:
            await utils.answer(
                message,
                self.strings("list_text"),
                reply_markup=self.generate_info_all_markup(page),
            )
    
    async def filteredVars(self, call, module, page=0):
        await call.edit(
            self.strings("vars_text").format(module=module),
            reply_markup=self.set_sections_markup(module, page),
        )

    async def showVars(self, call, module, page_num, section):
        await call.edit(
            self.strings("vars_text").format(module=module),
            reply_markup=self.generate_module_items(module, 1, page_num,section)
        )

    async def openFullVarValue(self, call, module, key, page_num, section):
        """Open full value of key"""
        var_value = getattr(self.lookup(module), key)
        if len(str(var_value)) > 300:
            var_value = f"{str(var_value)[:150]}...{len(str(var_value))-300}...{str(var_value)[-150:]}"
        await call.edit(
            f"<pre><code class='language-{module}-attrs'>{html.escape(str(var_value))}</code></pre>",
            reply_markup=[
                [
                    {
                        "text": "✍️",
                        "callback": self.waitVar,
                        "args": (module, key, page_num, section),
                    }
                ],
                [
                    {
                        "text": self.strings("back"),
                        "callback": self.showVars,
                        "args": (
                            module,
                            page_num,
                            section,
                        ),
                    }
                ]
            ],
        )

    async def waitVar(self, call, module, var, page_num, section):
        self.handle = [self.editVarValue, module, var, page_num, call]
        await call.edit(
            self.strings("waiting"),
            reply_markup=[
                {
                    "text": self.strings("back"),
                    "callback": self.setMenu,
                    "args": (module, page_num),
                },
            ],
        )

    async def editVarValue(self, new_value):
        module, var, page_num, call = self.handle[1:]
        try:
            new_value = ast.literal_eval(new_value)
        except (ValueError, SyntaxError):
            await call.edit(f"❌ Value/Syntax Error.\n<code>{str(new_value)}</code>",reply_markup=[
            [
                {
                "text": self.strings("back"),
                "callback": self.setMenu,
                "args": (module, page_num),
                }
            ]
        ])
            return
        setattr(self.lookup(module), var, new_value)
        self.handle = None
        await call.edit("✅",reply_markup=[
            {
                "text": self.strings("back"),
                "callback": self.setMenu,
                "args": (module, page_num),
            }
        ])

    async def showDB(self, call, module):
        await call.edit(
            self.strings("db_text").format(module=module),
            reply_markup=self.generate_module_items,
            args=(module, 2),
        )

    ##### Генератор #####

    def generate_info_all_markup(self, page_num=0):
        """Generate markup for inline form with 3x3 grid and navigation buttons"""
        items = list(self._db.items())
        markup = [[]]
        items_per_page = 3 * 4
        num_pages = len(items) // items_per_page + (
            1 if len(items) % items_per_page != 0 else 0
        )

        page_items = items[page_num * items_per_page : (page_num + 1) * items_per_page]
        for item in page_items:
            if len(markup[-1]) == 3:
                markup.append([])
            markup[-1].append(
                {
                    "text": f"{item[0]}" if self.lookup(item[0]) else f"[{item[0]}]",
                    "callback": self.inspect,
                    "args": (item[0], page_num),
                }
            )

        nav_markup = []
        if page_num > 0:
            nav_markup.extend(
                [
                    {
                        "text": "⇤" if page_num != 1 else " ",
                        "callback": self.change_main_menu_page,
                        "args": [0],
                    },
                    {
                        "text": "←",
                        "callback": self.change_main_menu_page,
                        "args": [page_num - 1],
                    },
                ]
            )
        else:
            nav_markup.extend(
                [
                    {
                        "text": " ",
                        "callback": self.change_main_menu_page,
                        "args": [page_num],
                    },
                    {
                        "text": " ",
                        "callback": self.change_main_menu_page,
                        "args": [page_num],
                    },
                ]
            )
        nav_markup.append(
            {
                "text": f"{page_num+1}/{num_pages}",
                "callback": self.change_main_menu_page,
                "args": [page_num],
            }
        )
        if page_num < num_pages - 1:
            nav_markup.extend(
                [
                    {
                        "text": "→",
                        "callback": self.change_main_menu_page,
                        "args": [page_num + 1],
                    },
                    {
                        "text": "⇥" if page_num != num_pages - 2 else " ",
                        "callback": self.change_main_menu_page,
                        "args": [num_pages - 1],
                    },
                ]
            )
        else:
            nav_markup.extend(
                [
                    {
                        "text": " ",
                        "callback": self.change_main_menu_page,
                        "args": [page_num],
                    },
                    {
                        "text": " ",
                        "callback": self.change_main_menu_page,
                        "args": [page_num],
                    },
                ]
            )

        if nav_markup:
            markup.append(nav_markup)

        markup.append([])
        markup[-1].append(
            {
                "text": self.strings("close_btn"),
                "action": "close",
            }
        )

        return markup

    def generate_module_items(self, module, mode, page_num=0,section=None):
        """Generates markup for module db/vars"""
        if mode == 1:  # vars
            raw_vars = self.lookup(module)
            items = self.filtered[section]
        elif mode == 2:  # db
            db = next((n for n in list(self._db.items()) if n[0] == module), None)
            if db:
                items = db[1].__dict__
            else:
                items = {}
        else:
            items = {}
        markup = [[]]
        items_per_page = 4 * 2
        num_pages = len(items) // items_per_page + (
            1 if len(items) % items_per_page != 0 else 0
        )
        page_items = list(items.items())[
            page_num * items_per_page : (page_num + 1) * items_per_page
        ]
        for item in page_items:
            if len(markup[-1]) == 2:
                markup.append([])
            key = item[0]
            value = item[1]
            if isinstance(value, (str, int, float, bool)):
                markup[-1].append(
                    {
                        "text": f"{key}",
                        "callback": self.openFullVarValue,
                        "args": (module, key, page_num, section),
                    }
                )
                markup[-1].append(
                    {
                        "text": f"edit",
                        "callback": self.waitVar,
                        "args": (module, key, page_num, section),
                    }
                )
            else:
                markup[-1].append(
                    {
                        "text": f"{key}",
                        "callback": self.openFullVarValue,
                        "args": (module, key, page_num, section),
                    }
                )
                markup[-1].append(
                    {
                        "text": "edit",
                        "callback": self.waitVar,
                        "args": (module, key, page_num, section),
                    }
                )
        nav_markup = []
        if page_num > 0:
            nav_markup.extend(
                [
                    {
                        "text": "⇤" if page_num != 1 else " ",
                        "callback": self.change_pag,
                        "args": [0],
                    },
                    {
                        "text": "←",
                        "callback": self.change_pag,
                        "args": [page_num - 1],
                    },
                ]
            )
        else:
            nav_markup.extend(
                [
                    {
                        "text": " ",
                        "callback": self.change_pag,
                        "args": [page_num],
                    },
                    {
                        "text": " ",
                        "callback": self.change_main_menu_page,
                        "args": [page_num],
                    },
                ]
            )
        nav_markup.append(
            {
                "text": f"{page_num+1}/{num_pages}",
                "callback": self.change_pag,
                "args": [page_num],
            }
        )
        if page_num < num_pages - 1:
            nav_markup.extend(
                [
                    {
                        "text": "→",
                        "callback": self.change_pag,
                        "args": [page_num + 1],
                    },
                    {
                        "text": "⇥" if page_num != num_pages - 2 else " ",
                        "callback": self.change_pag,
                        "args": [num_pages - 1],
                    },
                ]
            )
        else:
            nav_markup.extend(
                [
                    {
                        "text": " ",
                        "callback": self.change_pag,
                        "args": [page_num],
                    },
                    {
                        "text": " ",
                        "callback": self.change_pag,
                        "args": [page_num],
                    },
                ]
            )
        if nav_markup:
            markup.append(nav_markup)

        markup.append([])
        markup[-1].append(
            {
                "text": self.strings("back"),
                "callback": self.filteredVars,
                "args": (module, page_num),
            }
        )
        markup[-1].append(
            {
                "text": self.strings("close_btn"),
                "action": "close",
            }
        )
        return markup
        
    def set_sections_markup(self, module, page):
        sections = [
        "readableVars",
        "libVars",
        "func",
        "config",
        "hikka",
        "hikka_func",
        "hikkaVars",
        "module",
        "module_func",
        "idkWhatIsThis"
        ]
        markup = [[]]
        for section in sections:
            if len(markup[-1]) > 1:
                markup.append([])
            markup[-1].append(
                {
                    "text":  f"[{len(self.filtered[section])}] " + section,
                    "callback": self.showVars,
                    "args":(module,0,section)
                }
            )
        markup.append([
        {
        "text": self.strings("back"),
        "callback": self.setMenu,
        "args": (
                    module,
                    0,
                ),
        }
        ]
        )
        return markup
        

    ##### Генератор #####

    async def change_main_menu_page(self, call, page_num):
        """Change to the specified page"""
        await call.edit(
            self.strings("list_text"),
            reply_markup=self.generate_info_all_markup(page_num),
        )

    async def change_pag(self, call, page_num):
        """Change to the specified page"""
        await call.edit(
            self.strings("vars_text").format(module=call.args[0]),
            reply_markup=self.generate_module_items(
                call.args[0], call.args[1], page_num
            ),
        )