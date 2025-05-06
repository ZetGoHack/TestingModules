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

from .. import loader

def generator(
    rows: int,
    columns: int,
    *buttons: dict,
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

def buttons():
    pass

@loader.tds
class debugger(loader.Module):
    """Docstring"""
    async def cmdcmd():
        generator(3,3,)