__version__ = ("updated", 0, 4)
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
        self.starttime = scnds
        self.timers = {"white": scnds, "black": scnds}
        self.running = {"white": False, "black": False}
        self.started = {"white": False, "black": False}
        self.last_time = time.monotonic()
        self.t = None
    
    def minutes(self) -> int:
        return self.starttime // 60

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
        await self._turn("white")
        self.started["white"] = True
        self.started["black"] = False

    async def black(self): ##to use
        await self._turn("black")
        self.started["white"] = False
        self.started["black"] = True

    async def _turn(self, color):#func
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
        "invite": "{opponent} you have invited to play chess! Do you accept?\n\n",
        "settings_text": "⚙️ Current settings: \n🎛️ <b>Style:</b> {style}\n⏲️ <b>Timer:</b> {timer}\n<b>Host plays:</b> {color}",
        "updated": "✅ Updated!",
        "yes": "✅ Accept",
        "no": "❌ No",
        "declined": "❌ Invitation declined",
        "settings": "⚙️ Settings",
        "back": "↩️ Back",
        "available": "Available",
        "not_available": "Not available",
        "not_you": "You cannot click here",
        "random": "🎲 Random",
        "white": "⚪ White",
        "black": "⚫ Black",
        "timer": "{} min.",
        "blitz_text": "⚡ Blitz",
        "blitz_message": "Blitz-Blitz – speed without limits",
        "rapid_text": "⏱️ Rapid",
        "rapid_message": "Ponder your defeat",
        "no_clock_text": "❌ No clock",
        }
    strings_ru = {
        "noargs": "<emoji document_id=5370724846936267183>🤔</emoji> Вы не указали с кем играть",
        "whosthat": "<emoji document_id=5019523782004441717>❌</emoji> Я не нахожу такого пользователя",
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Одиночные шахматы? Простите, нет",
        "invite": "{opponent}, вас пригласили сыграть партию шахмат! Примите?\n\n",
        "settings_text": "⚙️ Текущие настройки: \n🎛️ <b>Стиль доски:</b> <code>{style}</code>\n⏱️ <b>Таймер:</b> {timer}\n<b>Хост играет за:</b> {color}",
        "updated": "✅ Обновлено!",
        "yes": "✅ Принимаю",
        "no": "❌ Нет",
        "declined": "❌ Приглашение отклонено",
        "settings": "⚙️ Настройки",
        "back": "↩️ Назад",
        "available": "Доступно",
        "not_available": "Недоступно",
        "not_you": "Вы не можете нажать сюда!",
        "random": "🎲 Рандом",
        "white": "⚪ Белые",
        "black": "⚫ Чёрные",
        "timer": "{} мин.",
        "blitz_text": "⚡ Блиц",
        "blitz_message": "Блиц-Блиц - скорость без границ",
        "rapid_text": "⏱️ Рапид",
        "rapid_message": "Обдумай своё поражение",
        "no_clock_text": "❌ Нет часов",
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
        games = self.get("games", {})
        if games:
            self.games = games
        else: self.games = {}
        self.gsettings = {
            "style": "figures-with-circles", # "figures", "letters"
        }
        self.pgn = {
            'event': '[Event "Chess Play With Module"]',
            'site': '[Site "https://t.me/nullmod/"]',
            'date': '[Date "{date}"]',
            'round': '[Round "{game_id}"]',
            'white': '[White "{player}"]',
            'black': '[Black "{player}"]',
            'result': '[Result "{result}"]',
        }
        
    async def _check_player(self, call, game_id, only_opponent=False):
        if isinstance(call, (BotInlineCall, InlineCall, InlineMessage)): 
            if call.from_user.id != self.games[game_id]["sender"]["id"]:
                if call.from_user.id != self.games[game_id]["opponent"]["id"]:
                    await call.answer(self.strings["not_available"])
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
        game: dict[str, Timer]  = self.games[game_id]
        await utils.answer(
            call,
            self.strings["invite"].format(opponent=self.games[game_id]["opponent"]["name"]) + self.strings['settings_text'].format(
                style=game['style'],

                timer=self.strings['available'] if isinstance(game['Timer'], bool) and game['Timer']
                else self.strings['timer'].format(game['Timer'].minutes()) if game["Timer"]
                else self.strings['not_available'],

                color=self.strings['random'] if game['host_plays'] == 'r' 
                else self.strings['white'] if game['host_plays'] == 'w'
                else self.strings['black']
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings["yes"],
                        "callback": self._init_game,
                        "args": (game_id,)
                    },
                    {
                        "text": self.strings["no"],
                        "callback": self._init_game,
                        "args": (game_id, "no")
                    }
                ],
                [
                    {
                        "text": self.strings["settings"],
                        "callback": self.settings,
                        "args": (game_id,)
                    }
                ]
            ],
            disable_security=True
        )

    async def settings(self, call, game_id):
        if not await self._check_player(call, game_id): return
        game = self.games[game_id]
        reply_markup = []
        if game["Timer"]:
            reply_markup.append([
                {"text":f"⏱️ Время", "callback":self._settings, "args": ("t", )}
            ])

        reply_markup.extend([
            [
                {"text":f"♟️ Цвет (хоста)", "callback":self._settings, "args": ("c", )}
            ],
            [
                {"text":f"🎛️ Стиль доски", "callback":self._settings, "args": ("s", )}
            ],
            [
                {"text": self.strings['back'], "callback": self._invite, "args": (game_id,)}
            ]])
        await utils.answer(
            call,
            self.strings['settings_text'].format(
                style=game['style'],

                timer=self.strings['available'] if isinstance(game['Timer'], bool) and game['Timer']
                else game['Timer'].minutes() if game["Timer"]
                else self.strings['not_available'],

                color=self.strings['random'] if game['host_plays'] == 'r' 
                else self.strings['white'] if game['host_plays'] == 'w'
                else self.strings['black']
            ),
            reply_markup=reply_markup
        )
    async def _settings(self, call, game_id, ruleset: str | list):
        game = self.games[game_id]
        reply_markup = []
        text = "🍓"
        if isinstance(ruleset, str):
            if ruleset == "t":
                text = "⏳"
                reply_markup.extend([
                    [
                        {"text": self.strings['blitz_text'], "action": "answer", "message": self.strings['blitz_message']}
                    ],
                    [
                        {"text": self.strings['timer'].format(3), "callback":self._settings, "args": ([game_id, 'Timer', 3])},
                        {"text": self.strings['timer'].format(5), "callback":self._settings, "args": ([game_id, 'Timer', 5])},
                    ],
                    [
                        {"text": self.strings['rapid_text'], "action": "answer", "message": self.strings['rapid_message']}
                    ],
                    [
                        {"text": self.strings['timer'].format(10), "callback":self._settings, "args": ([game_id, 'Timer', 10])},
                        {"text": self.strings['timer'].format(15), "callback":self._settings, "args": ([game_id, 'Timer', 15])},
                        {"text": self.strings['timer'].format(30), "callback":self._settings, "args": ([game_id, 'Timer', 30])},
                        {"text": self.strings['timer'].format(60), "callback":self._settings, "args": ([game_id, 'Timer', 60])}
                    ],
                    [
                        {"text": self.strings['no_clock_text'], "callback":self._settings, "args": (game_id, 'Timer', True)}
                    ]
                ])
            elif ruleset == "c":
                text = "♟️"
                reply_markup.extend([
                    [
                        {"text": self.strings['white'], "callback":self._settings, "args": ([game_id, 'host_plays', 'w'])},
                        {"text": self.strings['black'], "callback":self._settings, "args": ([game_id, 'host_plays', 'b'] )}
                    ],
                    [
                        {"text": self.strings['random'], "callback":self._settings, "args": ([game_id, 'host_plays', 'r'])}
                    ]
                ])
            elif ruleset == "s":
                text = "✏️"
                reply_markup.extend([
                    [{"text": "[♔⚪] Figures with circles", "callback":self._settings, "args": (game_id, 'style', 'figures-with-circles')}],
                    [{"text": "[♔] Figures", "callback":self._settings, "args": (game_id, 'style', 'figures')}],
                    [{"text": "[𝗞] Letters", "callback":self._settings, "args": (game_id, 'style', 'letters')}]
                ])

            reply_markup.append(
                [
                    {"text": self.strings['back'], "callback": self.settings, "args": (game_id,)}
                ]
            )

            await utils.answer(call, text, reply_markup=reply_markup)
        else:
            await call.answer("✅")
            if ruleset[1] == "style":
                self.set('style', ruleset[2])
            if ruleset[1] == "Timer" and isinstance(ruleset[2], int):
                self.games[ruleset[0]][ruleset[1]] = Timer(ruleset[2]*60)
            else:
                self.games[ruleset[0]][ruleset[1]] = ruleset[2]
            await self.settings(call, game_id)
            

    @loader.command(ru_doc="[reply/username/id] - предложить человеку сыграть партию")
    async def chess(self, message):
        """[reply/username/id] - propose a person to play a game"""
        sender, opponent = await self.get_players(message)
        if not sender or not opponent: return
        if sender['id'] == opponent['id']:
            await utils.answer(message, self.strings["playing_with_yourself?"])
            return
        if self.games:
            past_game =  next(reversed(self.games.values()))
            if not getattr(past_game, "game", None):
                self.games.pop(past_game['game_id'], None)
        if not self.games:
            game_id = 1
        else:
            game_id = max(self.games.keys()) + 1
        self.games[game_id] = {
            "game_id": game_id,
            "sender": sender,
            "opponent": opponent,
            "Timer": True if isinstance(message.peer_id, PeerUser) else False,
            "time": int(time.time()),
            "host_plays": "r", # r(andom), w(hite), b(lack)
            "style": self.gsettings['style'],
        }
        await self._invite(message, game_id)

    ############## Starting game... ############## 

    async def _init_game(self, call, game_id, ans="yes"):
        if not await self._check_player(call, game_id=game_id, only_opponent=True): return
        if ans == "no":
            self.games.pop(game_id, None)
            await utils.answer(call, self.strings["declined"])
            return
        if (turn := self.games[game_id].pop("host_plays")) == "r":
            turn = "w" if r.choice([0, 1]) == 0 else "b"
        self.games[game_id]["turn"] = turn
        await utils.answer(call, f"filler\n{self.games[game_id]}")

# TODO доделать настройки, кнопки