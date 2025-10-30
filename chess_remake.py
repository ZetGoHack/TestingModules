__version__ = ("updated", 2, 4) #######################
#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]

# meta developer: @nullmod
# requires: python-chess

# -      main      - #
from .. import loader, utils
from ..inline.types import BotInlineCall, InlineCall, InlineMessage
# -      func      - #
import asyncio
import chess
import chess.pgn
import random as r
import time
from datetime import datetime, timezone
# -      types     - #
from telethon.tl.types import PeerUser, Message
from typing import TypedDict
# -      end       - #

class Timer:
    def __init__(self, scnds):
        self.starttime = scnds
        self.timers = {"white": scnds, "black": scnds}
        self.running = {"white": False, "black": False}
        self.last_time = time.monotonic()
        self.t = None
    
    def minutes(self) -> int:
        return self.starttime // 60

    async def _count(self):
        while True:
            await asyncio.sleep(0.1)
            now = time.monotonic()
            elapsed = now - self.last_time
            self.last_time = now
            for color in ("white", "black"):
                if self.running[color]:
                    self.timers[color] = max(0, self.timers[color] - elapsed)

    async def start(self, from_color: str = "white"):
        self.last_time = time.monotonic()
        await self._turn(from_color)
        self.t = asyncio.create_task(self._count())

    async def switch(self):
        self.running["white"] = not self.running["white"]
        self.running["black"] = not self.running["black"]

    async def _turn(self, color):
        now = time.monotonic()
        e = now - self.last_time
        self.last_time = now
        for clr in ("white", "black"):
            if self.running[clr]:
                self.timers[clr] = max(0, self.timers[clr] - e)
        self.running = {"white": color == "white", "black": color == "black"}

    async def white_time(self):
        return round(self.timers["white"], 0)

    async def black_time(self):
        return round(self.timers["black"], 0)

    async def stop(self):
        if self.t:
            self.t.cancel()
        self.running = {"white": False, "black": False}

### Type annotations ###

class Player(TypedDict):
    id: int
    name: str

class TimerDict(TypedDict):
    timer: Timer
    timer_loop: bool
    timer_is_set: bool
    message: InlineCall

class GameParams(TypedDict):
    chosen_figure_coord: str

class Game(TypedDict):
    board: chess.Board
    message: InlineCall
    node: chess.pgn.Game
    state: str
    reason: str
    add_params: GameParams

class GameObj(TypedDict):
    game_id: int
    game: Game
    sender: Player
    opponent: Player
    Timer: TimerDict
    time: int
    host_plays: bool # True - white, False - black
    style: dict[str, str]

GamesDict = dict[str, GameObj]

### Type annotations ###

@loader.tds
class Chess(loader.Module):
    """A reworked version of the Chess module"""
    strings = {
        "name": "Chess",
        "noargs": "<emoji document_id=5370724846936267183>🤔</emoji> You did not specify who to play with",
        "whosthat": "<emoji document_id=5019523782004441717>❌</emoji> I cannot find such a user",
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Playing with yourself? Sorry, you can't",
        "invite": "{opponent} you have invited to play chess! Do you accept?\n\n",
        "settings_text": "⚙️ Current settings: \n\n    🎛️ <b>Style:</b> {style}\n    ⏲️ <b>Timer:</b> {timer}\n    ♟️ <b>Host plays:</b> {color}",
        "updated": "✅ Updated!",
        "yes": "✅ Accept",
        "no": "❌ No",
        "declined": "❌ Invitation declined",
        "settings": "⚙️ Settings",
        "time_btn": "⏱️ Time",
        "color_btn": "♟️ Host color",
        "style_btn": "🎛️ Board style",
        "fwc": "Figures + colors",
        "f": "Figures",
        "l": "Letters",
        "back": "↩️ Back",
        "available": "Available",
        "not_available": "Not available",
        "not_you": "You cannot click here",
        "opp_move": "Opponent's turn!",
        "random": "🎲 Random",
        "white": "⚪ White",
        "black": "⚫ Black",
        "timer": "{} min.",
        "blitz_text": "⚡ Blitz",
        "blitz_message": "Blitz-Blitz – speed without limits",
        "rapid_text": "⏱️ Rapid",
        "rapid_message": "Ponder your defeat",
        "no_clock_text": "❌ No clock",
        "step1": "🔁 [0%] Initialization... Creating board..",
        "step2": "🔁 [25%] Initialization... Setting style..",
        "step3": "🔁 [50%] Initialization... Choosing colors..",
        "step4": "🔁 [75%] Initialization... Almost there...",
        "step4.T": "🔁 [88%] Initialization... Connecting timer..",
        "step5": "✅ [100%] Done!",
        "timer_text": "♔ White: {}\n♚ Black: {}\n\n{}",
        "reason": "",
        "reason_timer": "Time is out!",
        "start_timer": "⏱️ Start",
        "waiting_for_start": "🔁 Waiting for timer to start...",
        }
    strings_ru = {
        "noargs": "<emoji document_id=5370724846936267183>🤔</emoji> Вы не указали с кем играть",
        "whosthat": "<emoji document_id=5019523782004441717>❌</emoji> Я не нахожу такого пользователя",
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Одиночные шахматы? Простите, нет",
        "invite": "{opponent}, вас пригласили сыграть партию шахмат! Примите?\n\n",
        "settings_text": "⚙️ Текущие настройки: \n\n    🎛️ <b>Стиль доски:</b> <code>{style}</code>\n    ⏱️ <b>Таймер:</b> {timer}\n    ♟️ <b>Хост играет за:</b> {color}",
        "updated": "✅ Обновлено!",
        "yes": "✅ Принимаю",
        "no": "❌ Нет",
        "declined": "❌ Приглашение отклонено",
        "settings": "⚙️ Настройки",
        "time_btn": "⏱️ Время",
        "color_btn": "♟️ Цвет (хоста)",
        "style_btn": "🎛️ Стиль доски",
        "fwc": "Фигуры + цвета",
        "f": "Фигуры",
        "l": "Буквы",
        "back": "↩️ Назад",
        "available": "Доступно",
        "not_available": "Недоступно",
        "not_you": "Вы не можете нажать сюда!",
        "opp_move": "Сейчас ход противника!",
        "random": "🎲 Рандом",
        "white": "⚪ Белые",
        "black": "⚫ Чёрные",
        "timer": "{} мин.",
        "blitz_text": "⚡ Блиц",
        "blitz_message": "Блиц-Блиц - скорость без границ",
        "rapid_text": "⏱️ Рапид",
        "rapid_message": "Обдумай своё поражение",
        "no_clock_text": "❌ Нет часов",
        "step1": "🔁 [0%] Инициализация... Создание доски..",
        "step2": "🔁 [25%] Инициализация... Ставлю стиль..",
        "step3": "🔁 [50%] Инициализация... Выбираю цвета",
        "step4": "🔁 [75%] Инициализация... Почти...",
        "step4.T": "🔁 [88%] Инициализация... Подключаю таймер..",
        "step5": "✅ [100%] Готово!",
        "timer_text": "♔ Белые: {}\n♚ Чёрные: {}\n\n{}",
        "reason": "",
        "reason_timer": "Время вышло!",
        "start_timer": "⏱️ Начать",
        "waiting_for_start": "🔁 Ожидаю включения таймера...",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "play_self",
                False,
                "Jst playing with urself",
                validator=loader.validators.Boolean(),
            )
        )
    
    async def client_ready(self):
        self.styles = {
            "figures-with-circles": {
            "r": "♖⚫", "n": "♘⚫", "b": "♗⚫", "q": "♕⚫", "k": "♔⚫", "p": "♙⚫",
            "R": "♖⚪", "N": "♘⚪", "B": "♗⚪", "Q": "♕⚪", "K": "♔⚪", "P": "♙⚪",
            "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            },
            "figures": {
            "r": "♜", "n": "♞", "b": "♝", "q": "𝗾", "k": "♚", "p": "♟",
            "R": "♖", "N": "♘", "B": "♗", "Q": "𝗤", "K": "♔", "P": "♙",
            "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            },
            "letters": {
            "r": "𝗿", "n": "𝗻", "b": "𝗯", "q": "𝗾", "k": "𝗸", "p": "𝗽",
            "R": "𝗥", "N": "𝗡", "B": "𝗕", "Q": "𝗤", "K": "𝗞", "P": "𝗣",
            "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            }
        }
        self.coords = {
            f"{col}{row}": "" for col in "abcdefgh"
            for row in range(1, 9)
        }
        games = self.get("games", {})
        if games:
            self.games = games
        else: self.games = {}
        self.games: GamesDict
        self.gsettings = {
            "style": "figures-with-circles", # "figures", "letters"
        }
        self.pgn = {
            'Event': "Chess Play In Module",
            'Site': "https://t.me/nullmod/",
            'Date': "{date}",
            'Round': "{game_id}",
            'White': "{player}",
            'Black': "{player}",
        }
        
    async def _check_player(self, call: InlineCall, game_id: int, only_opponent=False):
        if isinstance(call, (BotInlineCall, InlineCall, InlineMessage)):
            game = self.games[game_id]
            _from_id = call.from_user.id

            if _from_id != game["sender"]["id"]:
                if _from_id != game["opponent"]["id"]:
                    await call.answer(self.strings["not_available"])
                    return False
            elif _from_id == game["sender"]["id"] and only_opponent:
                await call.answer(self.strings["not_you"])
                return False
            elif not self.config["play_self"]:
                if game["host_plays"] == game["game"]["board"].turn and game["sender"]["id"] != _from_id:
                    await call.answer(self.strings["opp_move"])
                    return False
                elif game["host_plays"] != game["game"]["board"].turn and game["opponent"]["id"] != _from_id:
                    await call.answer(self.strings["opp_move"])
                    return False
        return True
    
    async def get_players(self, message: Message):
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

    async def _invite(self, call: InlineCall, game_id: int):
        if not await self._check_player(call, game_id): return
        game  = self.games[game_id]
        await utils.answer(
            call, 
            self.strings["invite"].format(opponent=utils.escape_html(self.games[game_id]["opponent"]["name"])) + self.strings['settings_text'].format(
                style=game['style'],

                timer=self.strings['available'] if game['Timer']['available'] and not game['Timer']['timer']
                else self.strings['timer'].format(game['Timer']['timer'].minutes()) if game['Timer']['timer']
                else self.strings['not_available'],
                
                color=self.strings['random'] if game['host_plays'] == 'r' 
                else self.strings['white'] if game['host_plays'] == True
                else self.strings['black']
            ),
            reply_markup = [
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

    async def settings(self, call: InlineCall, game_id: int):
        if not await self._check_player(call, game_id): return
        game = self.games[game_id]
        reply_markup = []
        if game["Timer"]["available"]:
            reply_markup.append([
                {"text": self.strings["time_btn"], "callback": self._settings, "args": (game_id, "t", )}
            ])

        reply_markup.extend([
            [
                {"text": self.strings["color_btn"], "callback": self._settings, "args": (game_id, "c", )}
            ],
            [
                {"text": self.strings["style_btn"], "callback": self._settings, "args": (game_id, "s", )}
            ],
            [
                {"text": self.strings['back'], "callback": self._invite, "args": (game_id,)}
            ]
        ])
        await utils.answer(
            call,
            self.strings['settings_text'].format(
                style=game['style'],

                timer=self.strings['available'] if game['Timer']['available'] and not game['Timer']['timer']
                else self.strings['timer'].format(game['Timer']['timer'].minutes()) if game['Timer']['timer']
                else self.strings['not_available'],

                color=self.strings['random'] if game['host_plays'] == 'r' 
                else self.strings['white'] if game['host_plays'] == True
                else self.strings['black']
            ),
            reply_markup=reply_markup,
            disable_security=True
        )
    async def _settings(self, call: InlineCall, game_id: int, ruleset: str | list):
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
                        {"text": self.strings['timer'].format(3), "callback":self._settings, "args": (game_id, ['Timer', 3])},
                        {"text": self.strings['timer'].format(5), "callback":self._settings, "args": (game_id, ['Timer', 5])},
                    ],
                    [
                        {"text": self.strings['rapid_text'], "action": "answer", "message": self.strings['rapid_message']}
                    ],
                    [
                        {"text": self.strings['timer'].format(10), "callback":self._settings, "args": (game_id, ['Timer', 10])},
                        {"text": self.strings['timer'].format(15), "callback":self._settings, "args": (game_id, ['Timer', 15])},
                        {"text": self.strings['timer'].format(30), "callback":self._settings, "args": (game_id, ['Timer', 30])},
                        {"text": self.strings['timer'].format(60), "callback":self._settings, "args": (game_id, ['Timer', 60])}
                    ],
                    [
                        {"text": self.strings['no_clock_text'], "callback":self._settings, "args": (game_id, ['Timer', True])}
                    ]
                ])
            elif ruleset == "c":
                text = "♟️"
                reply_markup.extend([
                    [
                        {"text": self.strings['white'], "callback":self._settings, "args": (game_id, ['host_plays', True])},
                        {"text": self.strings['black'], "callback":self._settings, "args": (game_id, ['host_plays', True] )}
                    ],
                    [
                        {"text": self.strings['random'], "callback":self._settings, "args": (game_id, ['host_plays', 'r'])}
                    ]
                ])
            elif ruleset == "s":
                text = "✏️"
                reply_markup.extend([
                    [{"text": "[♔⚪] " + self.strings["fwc"], "callback":self._settings, "args": (game_id, ['style', 'figures-with-circles'])}],
                    [{"text": "[♔] " + self.strings["f"], "callback":self._settings, "args": (game_id, ['style', 'figures'])}],
                    [{"text": "[𝗞] " + self.strings["l"], "callback":self._settings, "args": (game_id, ['style', 'letters'])}]
                ])

            reply_markup.append(
                [
                    {"text": self.strings['back'], "callback": self.settings, "args": (game_id,)}
                ]
            )

            await utils.answer(call, text, reply_markup=reply_markup, disable_security=True)
        else:
            await call.answer("✅")
            if ruleset[0] == "style":
                self.set('style', ruleset[1])
            if ruleset[0] == "Timer" and isinstance(ruleset[1], int):
                self.games[game_id]['Timer']['timer'] = Timer(ruleset[1]*60)
            else:
                self.games[game_id][ruleset[0]] = ruleset[1]
            await self.settings(call, game_id)
            

    @loader.command(ru_doc="[reply/username/id] - предложить человеку сыграть партию")
    async def chess(self, message: Message):
        """[reply/username/id] - propose a person to play a game"""
        sender, opponent = await self.get_players(message)
        if not sender or not opponent: return
        if sender['id'] == opponent['id'] and not self.config["play_self"]:
            await utils.answer(message, self.strings["playing_with_yourself?"])
            return
        if self.games:
            past_game =  next(reversed(self.games.values()))
            if not getattr(past_game, "game", None):
                self.games.pop(past_game['game_id'], None)
        if not self.games:
            game_id = str(1)
        else:
            game_id = str(max(map(int, self.games.keys())) + 1)
        self.games[game_id] = GameObj(
            game_id = game_id,
            sender = sender,
            opponent = opponent,
            Timer = {"available": True if isinstance(message.peer_id, PeerUser) else False, "timer": None, "timer_loop": False},
            time = int(time.time()),
            host_plays = "r", # r(andom), w(hite), b(lack)
            style = self.gsettings['style']
        )
        await self._invite(message, game_id)

    ############## Preparing all for game start... ##############

    async def _init_game(self, call: InlineCall, game_id: int, ans="yes"):
        if not await self._check_player(call, game_id=game_id, only_opponent=True): return
        if ans == "no":
            self.games.pop(game_id, None)
            await utils.answer(call, self.strings["declined"])
            return
        game = self.games[game_id]
        await utils.answer(call, self.strings["step1"])
        await asyncio.sleep(0.8)
        await utils.answer(call, self.strings["step2"])
        game["style"] = self.styles[game["style"]]
        await asyncio.sleep(0.8)
        await utils.answer(call, self.strings["step3"])
        if (turn := game["host_plays"]) == "r":
            turn = r.choice([True, False])
        game["host_plays"] = turn
        await asyncio.sleep(0.8)
        await utils.answer(call, self.strings["step4"])
        game["Timer"].pop("available", None)
        await asyncio.sleep(0.8)
        if isinstance(self.games[game_id]["Timer"]["timer"], Timer):
            await utils.answer(call, self.strings["step4.T"])
            await self._set_timer(call, game_id, call._units[call.unit_id]['chat'])
            await asyncio.sleep(0.8)
            return await utils.answer(call, self.strings["waiting_for_start"])
        await self._start_game(call, game_id)

    async def _set_timer(self, board_call: InlineCall, game_id: int, chat_id):
        timer = self.games[game_id]["Timer"]["timer"]
        self.games[game_id]["Timer"]["message"] = (
            await self.inline.form(self.strings["timer_text"].format(
                int(await timer.white_time()), 
                int(await timer.black_time()), 
                ""
                ), 
                chat_id,
                reply_markup = {"text": self.strings["start_timer"], "callback": self._start_timer, "args": (board_call, game_id,)},
                disable_security = True,
            )
        )

    @loader.loop(interval=1, autostart=True)
    async def main_loop(self):
        for game_id in self.games:
            if self.games[game_id]["Timer"]["timer_loop"] and not self.games[game_id]["Timer"].get("timer_is_set", False):
                async def timer_loop(game_id):
                    timer = self.games[game_id]["Timer"]["timer"]
                    await timer.start()
                    self.games[game_id]["Timer"]["timer_is_set"] = True
                    while self.games[game_id]["Timer"]["timer_loop"]:
                        if not any([await timer.white_time(), await timer.black_time()]):
                            self.games[game_id]["Timer"]["timer_loop"] = False
                            self.games[game_id]["game"]["reason"] = "reason_timer"
                        await self.games[game_id]["Timer"]["message"].edit(self.strings["timer_text"].format(
                            int(await timer.white_time()), 
                            int(await timer.black_time()), 
                            "" if self.games[game_id]["game"]["board"] else "⏹️ " + self.strings[self.games[game_id]["game"]["reason"]]
                            )
                        )
                        await asyncio.sleep(1)
                    await timer.stop()
                asyncio.create_task(timer_loop(game_id))
            if self.games[game_id]["game"].get("message", None):
                self.games[game_id]["game"]["message"].inline_manager._units[
                    self.games[game_id]["game"]["message"].unit_id
                ]["always_allow"] = True # для ругающегося на эту строку гпт - по неизвестно какой причине фреймворк в какое-то время попросту
                                         # забывает про отключение его проверки. мне это нужно, чтобы сам модуль брал на себя ответсвенность
                                         # проверки, кто может управлять доской, а до кого очередь ещё не дошла

    ############## Starting game... ############## 

    async def _start_timer(self, call: InlineCall, board_call: InlineCall, game_id: int):
        if not await self._check_player(call, game_id): return
        timer = self.games[game_id]["Timer"]
        timer["timer_loop"] = True
        await self._start_game(board_call, game_id)

    async def _start_game(self, call: InlineCall, game_id: int):
        if not await self._check_player(call, game_id): return
        game = self.games[game_id]
        node = chess.pgn.Game()
        pgn = self.pgn.copy()
        pgn["Date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        pgn["Round"] = str(game_id)
        pgn["White"] = game["sender"] if game["host_plays"] else game["opponent"]
        pgn["Black"] = game["opponent"] if game["host_plays"] else game["sender"]
        node.headers.update(pgn)
        game["game"] = {
            "board": chess.Board(),
            "message": call,
            "node": node,
            "state": "idle", # 'idle' - начальное состояние (показать ток доску с фигурами), 'in_choose' - игрок жамкнул на фигуру и нужно показать доступные ходы, 'the_end' - конец партии
            "add_params": {
                "chosen_figure_coord": "",
            }
        }
        await utils.answer(call, f"filler\n{utils.escape_html(str(self.games[game_id]))}", reply_markup={"text":"stop", "callback": lambda c, id: self.games[id]['Timer'].update({'timer_loop': not self.games[id]['Timer']['timer_loop']}), "args": (game_id,)}, disable_security=True)

# TODO начало игры (придумать текста, генерация доски (чтение и запись фигур из доски, отрисовка в разных стилях, отображение возможных ходов), возможность выгрузить pgn при нажатии на A1 5 раз подряд в любой момент игры, кнопки ничьи/сдачи), игра (отображение событий(шах), синхронизация с таймером), лень

    def idle(self, game_id: str):
        game = self.games[game_id]["game"]
        game["state"] = "idle"
        game["add_params"]["chosen_figure_coord"] = ""
        
    def choose(self, game_id: str, coord: str):
        game = self.games[game_id]["game"]
        game["state"] = "in_choose"
        game["add_params"]["chosen_figure_coord"] = coord
        
    def the_end(self, game_id: str):
        game = self.games[game_id]["game"]
        game["state"] = "in_choose"
        game["add_params"]["chosen_figure_coord"] = ""

    def _get_piece_symbol(self, game_id: int, coord: str) -> str:
        game = self.games[game_id]
        piece = game["game"]["board"].piece_at(chess.parse_square(coord))
        return game["style"][piece.symbol()] if piece else " "
    
    def _get_move_symbol(self, game_id: int, move: str) -> str:
        game = self.games[game_id]
        if len(move) == 5:
            return game["style"][
                "capture_promotion" if (move := chess.Move.from_uci(move))
                and game["game"]["board"].is_capture(move)
                else "promotion"
            ]
        else:
            return game["style"][
                "capture" if (move := chess.Move.from_uci(move))
                and game["game"]["board"].is_capture(move)
                else "move"
            ]
    
    def _get_available_moves(self, game_id: int, coord: str) -> list[str]:
        if not coord: return []
        game = self.games[game_id]
        coord = chess.parse_square(coord)
        moves = [move.uci() for move in game["game"]["board"].legal_moves if move.from_square == coord]
        return moves

    def _get_board_dict(self, game_id: int) -> dict[str, str]:
        game = self.games[game_id]
        coords = self.coords.copy()
        for coord in self.coords:
            coords[coord] = self._get_piece_symbol(game_id, coord)
        
        if game["game"]["state"] == "in_choose":
            choosen_coord = game["game"]["add_params"]["chosen_figure_coord"]
            for move in self._get_available_moves(game_id, choosen_coord):
                coord = move[2:4]
                coords[coord] = self._get_move_symbol(game_id, move)
        
        return coords

    async def update_board(self, game_id: int):
        game = self.games[game_id]["game"]

        reply_markup = utils.chunks(
            [
                {
                    "text": figure,
                    "callback": self.choose_coord,
                    "args": (game_id, coord),
                }
                for coord, figure in self._get_board_dict(game_id).items()
            ],
            8
        )
        await utils.answer(
            game["message"],
            self.strings["board"],
            reply_markup=reply_markup,
        )

    async def make_move(self, game_id: int, move: str):
        game = self.games[game_id]["game"]
        move = chess.Move.from_uci(move)
        game["board"].push(move)
        game["node"] = game["node"].add_variation(move)
    
    async def choose_coord(self, call: BotInlineCall, game_id: int, coord: str):
        if not self._check_player(call, game_id): return
        game = self.games[game_id]["game"]
        state = game["state"]

        if state == "idle":
            if self._get_available_moves(game_id, coord):
                self.choose(game_id, coord)
            return await self.update_board(game_id)
        
        elif state == "in_choose":
            if coord == game["add_params"]["chosen_figure_coord"]: # клик по той же фигуре
                self.idle(game_id)
                return await self.update_board(game_id)
            
            av_moves = self._get_available_moves(game_id, game["add_params"]["chosen_figure_coord"])
            coord_matches = [move for move in av_moves if coord in move]

            if len(coord_matches) == 1: # прост ход
                self.make_move(game_id, coord_matches[0])
                return await self.update_board(game_id)

            elif len(coord_matches) > 1: # пешка дошла до конца
                pass # TODO

            elif game["board"].piece_at(chess.parse_square(coord)): # другая фигура
                self.choose(game_id, coord)
                return await self.update_board(game_id)
            
            else: # в принципе нет там фигур
                self.idle(game_id)
                return await self.update_board(game_id)
        
        elif state == "the_end":
            pass

        else:
            await call.answer("ты игру сломал?")
            self.idle(game_id)
            return await self.update_board(game_id)