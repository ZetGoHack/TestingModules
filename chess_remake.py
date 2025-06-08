__version__ = ("updated", 0, 0)
#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]

# meta developer: @nullmod
# requires: python-chess

# meta developer: @nullmod

# -      main      - #
from .. import loader, utils
# -      func      - #
import asyncio
import random as r
import time
# -      types     - #
from telethon.tl.types import PeerUser
from ..inline.types import BotInlineCall, InlineCall, InlineMessage
# -      end       - #


class Timer:
    def __init__(self, scnds):#start
        self.timers = {"white": scnds, "black": scnds}
        self.running = {"white": False, "black": False}
        self.started = {"white": False, "black": False}
        self.last_time = time.monotonic()
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
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Playing with yourself? Sorry, you can't",
        "invite": "{} you have invited to play chess! Do you accept?",
        "yes": "✅ Yes",
        "no": "❌ No",
        "declined": "❌ Invitation declined",
        "settings": "⚙️ Settings",
        "not_your_game": "This is not your game!",
        "not_you": "You cannot click here",
        }
    strings_ru = {
        "noargs": "<emoji document_id=5370724846936267183>🤔</emoji> Вы не указали с кем играть",
        "whosthat": "<emoji document_id=5019523782004441717>❌</emoji> Я не нахожу такого пользователя",
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Одиночные шахматы? Простите, нет",
        "invite": "{}, вас пригласили сыграть партию шахмат! Примите?\n\n",
        "yes": "✅ Да",
        "no": "❌ Нет",
        "declined": "❌ Приглашение отклонено",
        "settings": "⚙️ Настройки",
        "not_your_game": "Это не ваша игра!",
        "not_you": "Вы не можете нажать сюда!",
    }
    
    async def client_ready(self):
        self.styles = {
            "figures-with-circles": {
            "r": "♖⚫", "n": "♘⚫", "b": "♗⚫", "q": "♕⚫", "k": "♔⚫", "p": "♙⚫",
            "R": "♖⚪", "N": "♘⚪", "B": "♗⚪", "Q": "♕⚪", "K": "♔⚪", "P": "♙⚪",
            },
            "figures": {
            "r": "♜", "n": "♞", "b": "♝", "q": "𝗾", "k": "♚", "p": "♟",
            "R": "♖", "N": "♘", "B": "♗", "Q": "𝗤", "K": "♔", "P": "♙",
            },
            "letters": {
            "r": "𝗿", "n": "𝗻", "b": "𝗯", "q": "𝗾", "k": "𝗸", "p": "𝗽",
            "R": "𝗥", "N": "𝗡", "B": "𝗕", "Q": "𝗤", "K": "𝗞", "P": "𝗣",
            }
        }
        self.games = {"filler": {
            "game_id": 0,
            }
        }
        self.gsettings = {
            "style": self.styles["figures-with-circles"], # "figures", "letters"
        }

    async def _check_player(self, call, game_id, only_opponent=False):
        if isinstance(call, (BotInlineCall, InlineCall, InlineMessage)): 
            if call.from_user.id != self.games[game_id]["sender"]["id"]:
                if call.from_user.id != self.games[game_id]["opponent"]["id"]:
                    await call.answer(self.strings["not_your_game"])
                    return False
            elif call.from_user.id == self.games[game_id]["sender"]["id"] and only_opponent:
                await call.answer(self.strings["not_you"])
                return False
        return True
    
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

    async def _invite(self, call, game_id):
        if not await self._check_player(call, game_id): return
        await utils.answer(
            call,
            self.strings["invite"].format(self.games[game_id]["opponent"]["name"]),
            reply_markup=[
                [
                    {
                        "text": self.strings["yes"],
                        "callback": self._init_game,
                        "args": (game_id, "")
                    },
                    {
                        "text": self.strings["no"],
                        "callback": self._init_game, #lambda call: utils.answer(call, self.strings["declined"])
                        "args": (game_id,)
                    }
                ],
                [
                    {
                        "text": self.strings["settings"],
                        "callback": self._settings,
                        "args": (game_id,)
                    }
                ]
            ],
            disable_security=True
        )

    async def _settings(self, call, game_id):
        if not await self._check_player(call, game_id): return
        game = self.games[game_id]
        self.gsettings["style"] = r.choice(list(self.styles.values()))
        await utils.answer(
            call,
            f"<b>Game ID:</b> {game_id}\n"
            f"<b>Host:</b> {game['sender']['name']} ({game['sender']['id']})\n"
            f"<b>Opponent:</b> {game['opponent']['name']} ({game['opponent']['id']})\n"
            f"<b>Style:</b> {game['style']}\n"
            f"<b>Timer:</b> {'Enabled' if game['Timer'] else 'Disabled'}\n"
            f"<b>Host plays:</b> {game['host_plays']}\n",
            reply_markup={
                "text": "⤴️ Back",
                "callback": self._invite,
                "args": (game_id)
            }
        )

    @loader.command(ru_doc="[reply/username/id] - предложить человеку сыграть партию в чате")
    async def chess(self, message):
        """[reply/username/id] - propose a person to play a game in the chat"""
        sender, opponent = await self.get_players(message)
        if not sender or not opponent: return
        if sender['id'] == opponent['id']:
            await utils.answer(message, self.strings["playing_with_yourself?"])
            return
        game_id = f"[#{next(reversed(self.games.values()))['game_id'] + 1}]"
        self.games[game_id] = {
            "game_id": next(reversed(self.games.values()))["game_id"] + 1,
            "sender": sender,
            "opponent": opponent,
            "Timer": True if isinstance(message.peer_id, PeerUser) else False,
            "time": int(time.time()),
            "host_plays": "r", # r(andom), w(hite), b(lack)
            "style": self.gsettings["style"],
        }
        await self._invite(message, game_id)

    async def _init_game(self, call, data):
        if not await self._check_player(call, game_id=data[0], only_opponent=True): return
        if len(data) == 1:
            self.games.pop(data[0], None)
            await utils.answer(call, self.strings["declined"])
            return
        game_id = data[0]
        if (turn := self.games[game_id].pop("host_plays")) == "r":
            turn = "w" if r.choice([0, 1]) == 0 else "b"
        self.games[game_id]["turn"] = turn
        await utils.answer(call, f"filler\n{self.games[game_id]}")