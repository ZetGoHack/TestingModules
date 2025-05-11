__version__ = (0,1,1)
(
#                     ⚠️⚠️⚠️                    #
#
#  Идея генератора был  взята и адаптирована из  #
#  модуля:  https://mods.xdesai.org/managedb.py  #
#              Разработчик: @xdesai              #
#                Спасибо большое!                #

#                     ⚠️⚠️⚠️                    #
)
# H:Mods Team [💎]
# meta developer: @nullmod

from .. import loader, utils

from typing import Callable

def _generator(
    rows: int,
    columns: int,
    buttons: list,
    page: int = 0,
    page_func: Callable = None,
    back_to: dict = None
): 
    """# Генератор списка кнопок
Принимает размер сетки кнопок, сами кнопки, поддерживает дополнения списка кнопок навигацией и кнопкой "назад",

**Принимает:**
- **rows:** `int <= 8`
- **columns:** `int | rows * columns <= 100`
- **buttons**: `[{'text':...,},...,{'text':...,}]`
- **page**: `int`
- **page_func**: `function`
- **back_to**: `dict`

**Возвращает:** 
- `list`(reply_markup)
    """
    if rows < 1 or columns < 1 or rows*columns > 100:
        raise ValueError("rows*columns должны быть между 1 и 100")
    per_page = rows * columns
    on_page = buttons
    reply_markup = []
    nav = False
    if len(buttons) > per_page:
        page_count = len(buttons) // per_page + (
                1 if len(buttons) % per_page != 0 else 0
            )
        on_page = buttons[per_page * page : per_page * (page + 1)]
        nav = True
    i = 0
    for _ in range(columns):
        reply_markup.append([])
        for _ in range(rows):
            if i < len(on_page):
                reply_markup[-1].append(on_page[i])
                i += 1
            else: break
    if nav:
        reply_markup.append(_nav_generator(page, page_count, page_func))
    if back_to:
        reply_markup.append([back_to])
    reply_markup.append({
        'text': module.strings['close'],
        'action': 'close'
    })
    return reply_markup

def _nav_generator(page, page_count, page_func):
    nav_markup = []
    if page > 0:
        nav_markup.extend(
            [
                {
                    "text": "⇤" if page != 1 else " ",
                    "callback": module.change_page,
                    "args": [0, page_func],
                },
                {
                    "text": "←",
                    "callback": module.change_page,
                    "args": [page - 1, page_func],
                },
            ]
        )
    else:
        nav_markup.extend(
            [
                {
                    "text": " ",
                    "callback": module.change_page,
                    "args": [page, page_func],
                },
                {
                    "text": " ",
                    "callback": module.change_page,
                    "args": [page, page_func],
                },
            ]
        )
    nav_markup.append(
        {
            "text": f"{page + 1}/{page_count}",
            "callback": module.change_page,
            "args": [page, page_func],
        }
    )
    if page < page_count - 1:
        nav_markup.extend(
            [
                {
                    "text": "→",
                    "callback": module.change_page,
                    "args": [page + 1, page_func],
                },
                {
                    "text": "⇥" if page != page_count - 2 else " ",
                    "callback": module.change_page,
                    "args": [page_count - 1, page_func],
                },
            ]
        )
    else:
        nav_markup.extend(
            [
                {
                    "text": " ",
                    "callback": module.change_page,
                    "args": [page, page_func],
                },
                {
                    "text": " ",
                    "callback": module.change_page,
                    "args": [page, page_func],
                },
            ]
        )
    return nav_markup

@loader.tds
class debugger(loader.Module):
    """Docstring"""
    strings = {
        'name': 'debugger',
        'main': 'List of modules',
        'module': '[{module}] List of variables',
        'back': '◀ Back',
        'close': '🔻 Close'
    }

    strings_ru = {
        'main': 'Список модулей',
        'module': '[{module}] Список содержимого',
        'back': '◀ Назад',
        'close': '🔻 Закрыть'
    }
    async def client_ready(self):
        global module
        module = self

    async def cmdcmd(self, message):
        """[module/nothing] open debugger"""
        await message.edit("🌓")
        await self._debugger(message)


    async def _debugger(self, call, page=0):
        await utils.answer(call, self.strings['main'], reply_markup=self._generate_main_list(page))

    async def _module(self, call, item, is_installed):
        pass # TODO

    async def _vars(self, call, item, page=0):
        pass # TODO

    async def _db(self, call, item, page=0):
        pass # TODO

    def _generate_main_list(self, page=0):
        buttons = []
        items = list(self._db.items())
        for item in items:
            buttons.append({
                'text': f'{item[0]}' if self.lookup(item[0]) else f'[{item[0]}]',
                'callback': self._module,
                'args': (item[0], True if self.lookup(item[0]) else False)
            })
        return _generator(3, 4, buttons, page, page_func=self._debugger)
        
    def _generate_module_list(self, page=0):
        back_to = {
            'text': self.strings['back'],
            'callback': self._debugger,
            'args': (page,)
        }

    def _generate_module_vars(self, page=0):
        pass # TODO

    def _generate_module_db(self, page=0):
        pass # TODO

    async def change_page(self, call, page, page_func):
        await page_func(call, page)