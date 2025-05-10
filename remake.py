__version__ = ("'","'","'")
# ░░░███░░░░░░░███░███
# ░░░░░█░░░░░░░█░░░█░█
# ░░░░█░░░███░░█░█░█░█
# ░░░█░░░░░░░░░█░█░█░█
# ░░░███░░░░░░░███░███
# H:Mods Team [💎]

# meta developer: @nullmod

from .. import loader, utils

def _generator(
    rows: int,
    columns: int,
    buttons: list,
    navigation: bool = False,
    back_to: dict = None
) -> list: 
    """# Генератор списка кнопок
Принимает размер сетки кнопок, сами кнопки, поддерживает дополнения списка кнопок навигацией и кнопкой назад,

**Принимает:**
- **rows:** `int <= 8`
- **columns:** `int | rows * columns <= 100`
- **buttons**: `[{'text':...,},...,{'text':...,}]`
- **navigation**: `bool`
- **back_to**: `dict`

**Возвращает:** 
- `list`(reply_markup)
"""
    pass
    reply_markup = []

@loader.tds
class debugger(loader.Module):
    """Docstring"""
    strings = {
        'name': 'debugger',
        'main': 'List of modules',
        'module': '[{module}] List of variables',
        'back': '◀ Back'
    }

    strings_ru = {
        'main': 'Список модулей',
        'module': '[{module}] Список содержимого',
        'back': '◀ Назад'
    }

    async def cmdcmd(self, message):
        """[module/nothing] open debugger"""
        await message.edit("🌓")
        await self._debugger(message)


    async def _debugger(self, call, page=1):
        await utils.answer(call, self.strings['main'], reply_markup=self._generate_main_list(page))

    async def _module(self, call):
        pass

    def _generate_main_list(self, page=1):
        buttons = []
        items = list(self._db.items())
        for item in items:
            buttons.append({
                'text': f'{item[0]}' if self.lookup(item[0]) else f'[{item[0]}]',
                'callback': self._generate_module_list,
                'args': (item[0],)
            })
        return _generator(3, 4, buttons)
        
    def _generate_module_list(self, page):
        back_to = {
            'text': self.strings['back'],
            'callback': self._debugger,
            'args': (page,)
        }