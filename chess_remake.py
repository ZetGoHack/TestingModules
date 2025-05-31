__version__ = ("updated", 0, 0)
#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]

# meta developer: @nullmod
# requires: python-chess

from .. import loader, utils

import asyncio, time, hashlib
from telethon.tl.types import PeerUser

class Timer:
    def __init__(self, scnds):#start
        self.timers = {"white": scnds, "black": scnds}
        self.running = {"white": False, "black": False}
        self.started = {"white": False, "black": False}
        self.last_time = time.monotonic()#Monotonic clock, cannot go backward
        self.t = None
    async def _count(self):#func
        while True:
            await asyncio.sleep(0.1)
            now = time.monotonic()
            elapsed = now - self.last_time
            self.last_time = now
            for color in ("white", "black"):
                if self.running[color]:
                    self.timers[color] = max(0, self.timers[color] - elapsed)

    async def start(self): ##to use
        self.last_time = time.monotonic()
        self.t = asyncio.create_task(self._count())

    async def white(self): ##to use
        await self.turn("white")
        self.started["white"] = True
        self.started["black"] = False

    async def black(self): ##to use
        await self.turn("black")
        self.started["white"] = False
        self.started["black"] = True

    async def turn(self, color):#func
        now = time.monotonic()
        e = now - self.last_time
        self.last_time = now
        for clr in ("white", "black"):
            if self.running[clr]:
                self.timers[clr] = max(0, self.timers[clr] - e)
        self.running = {"white": color == "white", "black": color == "black"}

    async def white_time(self): ##to use
        return round(self.timers["white"], 0)

    async def black_time(self): ##to use
        return round(self.timers["black"], 0)

    async def stop(self):
        if self.t:
            self.t.cancel()
        self.running = {"white": False, "black": False}
        self.timers = {"white": self.timers["white"], "black": self.timers["black"]}
        self.started = {"white": False, "black": False}

    async def clear(self): ##to use
        if self.t:
            self.t.cancel()
        self.timers = {"white": 0, "black": 0}
        self.running = {"white": False, "black": False}
        self.started = {"white": False, "black": False}
        self.t = None

@loader.tds
class Chess(loader.Module):
    """A reworked version of the Chess module"""
    strings = {
        "name": "Chess",
        "noargs": "<emoji document_id=5370724846936267183>🤔</emoji> You did not specify who to play with",
        "whosthat": "<emoji document_id=5019523782004441717>❌</emoji> I cannot find such a user",
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Playing alone? Sorry, you can't",
        "test1": "<emoji document_id=5978568938156461643>🔄</emoji> Game {} created",
        "test2": "White: {} ({})",
        "test3": "Black: {} ({})",
        "test4": "Timer: {}",
        "": "",
        }
    strings_ru = {
        "noargs": "<emoji document_id=5370724846936267183>🤔</emoji> Вы не указали с кем играть",
        "whosthat": "<emoji document_id=5019523782004441717>❌</emoji> Я не нахожу такого пользователя",
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Одиночные шахматы? Простите, нет",
        "test1": "<emoji document_id=5978568938156461643>🔄</emoji> Игра {} создана",
        "test2": "Белые: {} ({})",
        "test3": "Чёрные: {} ({})",
        "test4": "Таймер: {}",
    }
    
    async def client_ready(self):
        self.games = {"filler": {
            "game_id": 0,
            }
        }

    async def get_players(self, message):
        sender = {
            "id": message.from_id.user_id if isinstance(message.peer_id, PeerUser) else message.sender.id,
            "name": (await self.client.get_entity(message.from_id if isinstance(message.peer_id, PeerUser) else message.sender.id)).first_name
        }
        if message.is_reply:
            r = await message.get_reply_message()
            opponent = r.sender
            opp_id = opponent.id
            opp_name = opponent.first_name
        else:
            args = utils.get_args(message)
            if len(args)==0:
                await utils.answer(message, self.strings["noargs"])
                return (None, None)
            opponent = args[0]
            try:
                if opponent.isdigit():
                    opp_id = int(opponent)
                    opponent = await self.client.get_entity(opp_id)
                    opp_name = opponent.first_name
                else:
                    opponent = await self.client.get_entity(opponent)
                    opp_name = opponent.first_name
                    opp_id = opponent.id
            except:
                await utils.answer(message, self.strings["whosthat"])
                return (None, None)
        opponent = {
            "id": opp_id,
            "name": opp_name
        }
        return (sender, opponent)

    @loader.command(ru_doc="[reply/username/id] - предложить человеку сыграть партию в чате")
    async def chess(self, message):
        """[reply/username/id] - propose a person to play a game in the chat"""
        sender, opponent = await self.get_players(message)
        if not sender or not opponent: return
        if sender['id'] == opponent['id']:
            await utils.answer(message, self.strings["playing_with_yourself?"])
        game_id = f"[#{next(reversed(self.games.values()))['game_id'] + 1}]"
        self.games[game_id] = {
            "game_id": next(reversed(self.games.values()))["game_id"] + 1,
            "sender": sender,
            "opponent": opponent,
            "Timer": True if isinstance(message.peer_id, PeerUser) else False,
            "time": int(time.time())
        }
        await utils.answer(message, f"{self.strings['test1'].format(game_id)}\n"
                                    f"{self.strings['test2'].format(sender['name'], sender['id'])}\n"
                                    f"{self.strings['test3'].format(opponent['name'], opponent['id'])}\n"
                                    f"{self.strings['test4'].format('Enabled' if self.games[game_id]['Timer'] else 'Disabled')}")