__version__ = (2, 0, "9-beta") #######################
#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███
#H:Mods Team [💎]

# meta developer: @nullmod
# requires: python-chess gdown

import asyncio
import chess
import chess.engine
import chess.pgn
import copy
import logging
import os
import random as r
import time

from telethon.tl.types import PeerUser, User, Message
from datetime import datetime, timezone
from typing import TypedDict, Literal

from .. import loader, utils
from ..inline.types import BotInlineCall, InlineCall, InlineMessage

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
        if from_color == "restore":
            if self.running["white"]:
                from_color = "white"
            else:
                from_color = "black"
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

    def restore(self, white_time: float, black_time: float, running: dict):
        self.timers["white"] = white_time
        self.timers["black"] = black_time
        self.running = running

    def backup(self) -> dict:
        return {
            "white_time": self.timers["white"],
            "black_time": self.timers["black"],
            "running": self.running
        }

    async def stop(self):
        if self.t:
            self.t.cancel()
        self.running = {"white": False, "black": False}

class Player(TypedDict):
    id: int
    name: str
    color: bool | None  # True - white, False - black

class TimerDict(TypedDict):
    timer: Timer
    timer_loop: bool
    timer_is_set: bool
    message: InlineCall

class GameParams(TypedDict):
    chosen_figure_coord: str
    reason_of_ending: str
    promotion_move: str
    winner_color: bool | None
    resigner_color: bool | None 
    draw_offerer: bool | None

class Game(TypedDict):
    board: chess.Board
    message: InlineCall
    root_node: chess.pgn.Game
    curr_node: chess.pgn.Game
    state: str
    reason: str
    add_params: GameParams
    bot: chess.engine.SimpleEngine | None

class GameObj(TypedDict):
    game_id: str
    vs_bot: bool
    bot_elo: int
    game: Game
    sender: Player
    opponent: Player
    Timer: TimerDict
    time: int
    host_plays: bool # True - white, False - black
    style: dict[str, str]

    @staticmethod
    async def restore(host, backup) -> "GameObj":
        pass

class GameBackup:
    game_id: int
    backup: Literal[True]

GamesDict = dict[str, GameObj]

logger = logging.getLogger(__name__)

def install_stockfish() -> str | None:
    import platform
    import gdown
    import zipfile
    system = platform.system()
    if system == "Windows":
        url = "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64.zip"
    elif system == "Linux":
        if platform.machine().lower() == "aarch64":
            url = "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-android-armv8.tar"
        else:
            url = "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64.tar"
    else:
        return None
    file_name = url.split("/")[-1]
    try:
        gdown.download(url, file_name, quiet=True)
        if file_name.endswith(".zip"):
            with zipfile.ZipFile(file_name, 'r') as file:
                file.extractall()
        elif file_name.endswith(".tar"):
            import tarfile
            with tarfile.open(file_name, 'r') as file:
                file.extractall()    # noqa: S202
        os.remove(file_name)

        return find_stfsh_exe()
    except Exception:
        logger.exception("Failed to install Stockfish")
        return None

def find_stfsh_exe() -> str | None:
    for root, _, files in os.walk("./stockfish"):
        for file in files:
            if "stockfish" in file.lower():
                return os.path.join(root, file)

def check_path(path: str) -> bool:
    return os.path.isfile(path)


@loader.tds
class Chess(loader.Module):
    """A reworked version of the Chess module"""
    strings = {
        "": "",
        "name": "Chess",
        "not_int_err": "❌ The value you entered is not a number",
        "out_of_range_err": "❌ The value you entered is out of range (1400-3200)",
        "stockfish_installed": "✅ Stockfish installed successfully! Path to binary: <code>{path}</code>",
        "stockfish_install_failed": "❌ Stockfish installation failed. Check logs for more info",
        "stockfish_not_found": "❌ Stockfish binary not found. You can install it by clicking the button below",
        "install_stockfish": "⬇️ Install Stockfish",
        "installing": "🔁 Installing...",
        "noargs": "<emoji document_id=5370724846936267183>🤔</emoji> You did not specify who to play with",
        "whosthat": "<emoji document_id=5019523782004441717>❌</emoji> I cannot find such a user",
        "not_a_user": "<emoji document_id=5019523782004441717>❌</emoji> This is not a user",
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Playing with yourself? Sorry, you can't",
        "invite": "{opponent} you have invited to play chess! Do you accept?\n\n",
        "invite_bot": "{opponent}, do you want to play against a bot?\n\n",
        "not_invite": "{opponent}, before starting the game, would you like to check the settings?\n\n",
        "is_someone_wanna_play": "♟️ Anyone wants to play chess? Click the button below to start a game!",
        "settings_text": "⚙️ Current settings: \n\n    🎛️ <b>Style:</b> {style}\n    ⏲️ <b>Timer:</b> {timer}\n    ♟️ <b>Host plays:</b> {color}",
        "bot_elo": "🧠 <b>Bot ELO</b>: <code>{elo}</code>",
        "updated": "✅ Updated!",
        "yes": "✅ Accept",
        "bot_yes": "✅ Play",
        "i_wanna": "✅ I want to!",
        "no": "❌ No",
        "declined": "❌ Invitation declined",
        "settings": "⚙️ Settings",
        "bot_elo_btn": "🧠 Bot ELO",
        "time_btn": "⏱️ Time",
        "color_btn": "♟️ Host color",
        "style_btn": "🎛️ Board style",
        "figures-with-circles": "Figures + colors",
        "figures": "Figures",
        "letters": "Letters",
        "figures-with-comb-letters": "Figures + combined letters",
        "figures-with-cyr-letters": "Figures + cyrillic letters",
        "figures-with-latin-letters": "Figures + latin letters",
        "back": "↩️ Back",
        "set_btn": "✍️ Set value",
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
        "board": "Game <code>#{}</code>\n♔ White - {}\n♚ Black - {}\n\nIt's <b>{}</b>'s turn\n<b>{}</b>\n<blockquote>{}</blockquote>",
        "no_moves": "No moves for this piece!",
        "check": "❗ Check!",
        "checkmate": "🛑 Checkmate! {winner} wins!",
        "time_is_up": "⌛ {loser}'s time is up! {winner} wins!",
        "stalemate": "🤝 Stalemate!",
        "insufficient_material": "🤝 Draw! Insufficient material to win!",
        "seventyfive_moves": "🤝 Draw! 75-move rule!",
        "fivefold_repetition": "🤝 Draw! Fivefold repetition!",
        "resign": "🏳️ Player {loser} has resigned!",
        "draw": "🤝 Players agreed to a draw!",
        "can_not_move": "You cannot make moves right now!",
        "choose_promotion": "Choose a piece for promotion!",
        "resign_check": "Are you sure you want to resign?",
        "resign_yes": "🏳️ Resign",
        "resign_no": "❌ Cancel",
        "resign_not_you": "You are not resigning player!",
        "draw_offer": "🤝 {} offer a draw!",
        "draw_yes": "🤝 Accept",
        "draw_not_you": "You cannot accept your own offer!",
        "game_ended": "Game ended. You cannot make moves.",
    }

    strings_ru = {
        "not_int_err": "❌ Введённое значение - не число",
        "out_of_range_err": "❌ Введённое значение - вне диапазона (1400-3200)",
        "stockfish_installed": "✅ Stockfish успешно установлен! Путь к бинарнику: <code>{path}</code>",
        "stockfish_install_failed": "❌ Не удалось установить Stockfish. Смотрите логи",
        "stockfish_not_found": "❌ Бинарник Stockfish не найден. Вы можете установить его, нажав на кнопку ниже",
        "install_stockfish": "⬇️ Установить Stockfish",
        "installing": "🔁 Установка...",
        "noargs": "<emoji document_id=5370724846936267183>🤔</emoji> Вы не указали с кем играть",
        "whosthat": "<emoji document_id=5019523782004441717>❌</emoji> Я не нахожу такого пользователя",
        "not_a_user": "<emoji document_id=5019523782004441717>❌</emoji> Это не пользователь",
        "playing_with_yourself?": "<emoji document_id=5384398004172102616>😈</emoji> Одиночные шахматы? Простите, нет",
        "invite": "{opponent}, вас пригласили сыграть партию шахмат! Примите?\n\n",
        "invite_bot": "{opponent}, вы хотите сыграть против бота?\n\n",
        "not_invite": "{opponent}, перед началом игры, не желаете ли глянуть в настройки?\n\n",
        "is_someone_wanna_play": "♟️ Кто-нибудь хочет сыграть в шахматы? Нажмите на кнопку ниже, чтобы начать игру!",
        "settings_text": "⚙️ Текущие настройки: \n\n    🎛️ <b>Стиль доски:</b> <code>{style}</code>\n    ⏱️ <b>Таймер:</b> {timer}\n    ♟️ <b>Хост играет за:</b> {color}",
        "bot_elo": "🧠 <b>ELO Бота</b>: <code>{elo}</code>",
        "updated": "✅ Обновлено!",
        "yes": "✅ Принимаю",
        "bot_yes": "✅ Играть",
        "i_wanna": "✅ Я хочу!",
        "no": "❌ Нет",
        "declined": "❌ Приглашение отклонено",
        "settings": "⚙️ Настройки",
        "bot_elo_btn": "🧠 Эло Бота",
        "time_btn": "⏱️ Время",
        "color_btn": "♟️ Цвет (хоста)",
        "style_btn": "🎛️ Стиль доски",
        "figures-with-circles": "Фигуры + цвета",
        "figures": "Фигуры",
        "letters": "Буквы",
        "figures-with-comb-letters": "Фигуры + комбинированные буквы",
        "figures-with-cyr-letters": "Фигуры + кириллические буквы",
        "figures-with-latin-letters": "Фигуры + латинские буквы",
        "back": "↩️ Назад",
        "set_btn": "✍️ Установить",
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
        "board": "Партия <code>#{}</code>\n♔ Белые - {}\n♚ Чёрные - {}\n\nСейчас ходят <b>{}</b>\n<b>{}</b>\n<blockquote>{}</blockquote>",
        "no_moves": "Для этой фигуры нет ходов!",
        "check": "❗ Шах!",
        "checkmate": "🛑 Шах и мат! Победил(а) {winner}!",
        "time_is_up": "⌛ Время у {loser} истекло! Победил(а) {winner}!",
        "stalemate": "🤝 Пат!",
        "insufficient_material": "🤝 Ничья! Недостаточно материала для победы!",
        "seventyfive_moves": "🤝 Ничья! Правило 75 ходов!",
        "fivefold_repetition": "🤝 Ничья! Пятикратное повторение ходов!",
        "resign": "🏳️ Игрок {loser} сдался!",
        "draw": "🤝 Игроки согласились на ничью!",
        "can_not_move": "Вы не можете делать ходы в данный момент!",
        "choose_promotion": "Выберите фигуру для превращения!",
        "resign_check": "Вы действительно хотите сдаться?",
        "resign_yes": "🏳️ Сдаться",
        "resign_no": "❌ Отмена",
        "resign_not_you": "Вы не тот игрок, который сдаётся!",
        "draw_offer": "🤝 {} предлагают ничью!",
        "draw_yes": "🤝 Согласиться",
        "draw_not_you": "Вы не можете согласиться на своё предложение!",
        "game_ended": "Игра завершена. Вы не можете делать ходы.",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "play_self",
                False,
                "Allows you to make moves without turn checks (also, you can play with yourself)",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "stockfish_path",
                None,
                "Path to stockfish engine",
            ),
        )
    
    async def client_ready(self):
        self._last_backup = 0
        self.styles = {
            "figures-with-circles": {
                "symbol": "[♔⚪] ",
                "r": "♖⚫", "n": "♘⚫", "b": "♗⚫", "q": "♕⚫", "k": "♔⚫", "p": "♙⚫",
                "R": "♖⚪", "N": "♘⚪", "B": "♗⚪", "Q": "♕⚪", "K": "♔⚪", "P": "♙⚪",
                "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            },
            "figures": {
                "symbol": "[♔] ",
                "r": "♜", "n": "♞", "b": "♝", "q": "𝗾", "k": "♚", "p": "♟",
                "R": "♖", "N": "♘", "B": "♗", "Q": "𝗤", "K": "♔", "P": "♙",
                "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            },
            "letters": {
                "symbol": "[𝗞] ",
                "r": "𝗿", "n": "𝗻", "b": "𝗯", "q": "𝗾", "k": "𝗸", "p": "𝗽",
                "R": "𝗥", "N": "𝗡", "B": "𝗕", "Q": "𝗤", "K": "𝗞", "P": "𝗣",
                "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            },
            "figures-with-cyr-letters": {
                "symbol": "[♔Б] ",
                "r": "♖Ч", "n": "♘Ч", "b": "♗Ч", "q": "♕Ч", "k": "♔Ч", "p": "♙Ч",
                "R": "♖Б", "N": "♘Б", "B": "♗Б", "Q": "♕Б", "K": "♔Б", "P": "♙Б",
                "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            },
            "figures-with-latin-letters": {
                "symbol": "[♔W] ",
                "r": "♖B", "n": "♘B", "b": "♗B", "q": "♕B", "k": "♔B", "p": "♙B",
                "R": "♖W", "N": "♘W", "B": "♗W", "Q": "♕W", "K": "♔W", "P": "♙W",
                "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            },
            "figures-with-comb-letters": {
                "symbol": "[♔ⷱ] ",
                "r": "♖ⷱ", "n": "♘ⷱ", "b": "♗ⷱ", "q": "♕ⷱ", "k": "♔ⷱ", "p": "♙ⷱ",
                "R": "♖ⷠ", "N": "♘ⷠ", "B": "♗ⷠ", "Q": "♕ⷠ", "K": "♔ⷠ", "P": "♙ⷠ",
                "move": "●", "capture": "×", "promotion": "↻", "capture_promotion": "×↻",
            },
        }
        self.coords = {
            f"{col}{row}": "" for row in range(1, 9)
            for col in "hgfedcba"
        }
        self.games: GamesDict = self.get("games_backup", {})
        self.pgn = {
            'Event': "Chess Play In Module",
            'Site': "https://t.me/nullmod/",
            'Date': "{date}",
            'Round': "{game_id}",
            'White': "{player}",
            'Black': "{player}",
        }
        if (path := find_stfsh_exe()):
            self.config["stockfish_path"] = path

    async def _check_player(self, call: InlineCall | Message | None, game_id: str, only_opponent: bool = False, skip_turn_check: bool = False) -> bool:
        if isinstance(call, (BotInlineCall, InlineCall, InlineMessage)):
            game = self.games[game_id]
            _from_id = call.from_user.id

            if game.get("game", None) and game["game"]["state"] == "the_end":
                await call.answer(self.strings["game_ended"], show_alert=True)
                return
            if _from_id != game["sender"]["id"] and _from_id != game["opponent"]["id"]:
                    await call.answer(self.strings["not_available"])
                    return False
            if _from_id == game["sender"]["id"] and only_opponent and not self.config["play_self"]:
                await call.answer(self.strings["not_you"])
                return False
            elif not self.config["play_self"] and game.get("game", None) and not skip_turn_check:
                if game["sender"]["color"] == game["game"]["board"].turn and game["sender"]["id"] != _from_id:
                    await call.answer(self.strings["opp_move"])
                    return False
                elif game["opponent"]["color"] == game["game"]["board"].turn and game["opponent"]["id"] != _from_id:
                    await call.answer(self.strings["opp_move"])
                    return False
        return True

    async def install_stockfish(self, call: InlineCall):
        await utils.answer(call, self.strings["installing"])
        path = install_stockfish()
        if path:
            self.config["stockfish_path"] = path
            await utils.answer(call, self.strings["stockfish_installed"].format(path=path))
        else:
            await utils.answer(call, self.strings["stockfish_install_failed"])

    async def get_players(self, message: Message | InlineCall, sender: dict = None, sender_only: bool = False, opponent_only: bool = False):
        if not sender:
            sender = {
                "id": message.sender_id,
                "name": (await self.client.get_entity(message.sender_id)).first_name
            }
        if sender_only:
            return sender

        if isinstance(message, InlineCall):
            opp_id = message.from_user.id
            opp_name = message.from_user.first_name

        elif message.is_reply:
            r = await message.get_reply_message()
            opponent = r.sender
            if not isinstance(opponent, User):
                await utils.answer(message, self.strings["not_a_user"])
                return (sender, None)
            opp_id = opponent.id
            opp_name = opponent.first_name
        else:
            args = utils.get_args(message)

            if len(args)==0:
                return (sender, None)

            opponent = args[0]
            try:
                if opponent.isdigit():
                    opp_id = int(opponent)
                    opponent = await self.client.get_entity(opp_id)

                    if not isinstance(opponent, User):
                        await utils.answer(message, self.strings["not_a_user"])
                        return (sender, None)
                    opp_name = opponent.first_name
                else:
                    opponent = await self.client.get_entity(opponent)

                    if not isinstance(opponent, User):
                        await utils.answer(message, self.strings["not_a_user"])
                        return (sender, None)

                    opp_name = opponent.first_name
                    opp_id = opponent.id
            except ValueError:
                await utils.answer(message, self.strings["whosthat"])
                return (sender, None)

        opponent = {
            "id": opp_id,
            "name": opp_name
        }
        if opponent_only:
            return opponent

        return (sender, opponent)

    async def _invite(self, call: InlineCall, game_id: str):
        if not await self._check_player(call, game_id): return
        game  = self.games[game_id]

        await utils.answer(
            call,
            self.strings["invite_bot" if game["vs_bot"] else "invite" if not game.get("alr_accepted", False) else "not_invite"].format(
                opponent=utils.escape_html(self.games[game_id]["opponent"]["name"])
            ) + self._get_settings_text(game_id),
            reply_markup = [
                [
                    {
                        "text": self.strings["bot_yes" if game["vs_bot"] else "yes"],
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

    async def settings(self, call: InlineCall, game_id: str):
        if not await self._check_player(call, game_id): return
        game = self.games[game_id]
        reply_markup = []

        if game["vs_bot"]:
            reply_markup.append([
                {"text": self.strings["bot_elo_btn"], "callback": self._settings, "args": (game_id, "e")}
            ])

        if game["Timer"]["available"]:
            reply_markup.append([
                {"text": self.strings["time_btn"], "callback": self._settings, "args": (game_id, "t",)}
            ])

        reply_markup.extend([
            [
                {"text": self.strings["color_btn"], "callback": self._settings, "args": (game_id, "c",)}
            ],
            [
                {"text": self.strings["style_btn"], "callback": self._settings, "args": (game_id, "s",)}
            ],
            [
                {"text": self.strings['back'], "callback": self._invite, "args": (game_id,)}
            ]
        ])
        await utils.answer(
            call,
            self._get_settings_text(game_id),
            reply_markup=reply_markup,
            disable_security=True
        )

    async def _elo_validator(self, call: InlineCall, data, game_id: str):
        reply_markup = {"text": self.strings['back'], "callback": self._settings, "args": (game_id, "e")}

        if not str(data).isdigit():
            return await utils.answer(call, self.strings["not_int_err"], reply_markup=reply_markup)
        if not 1400 <= int(data) <= 3190:
            return await utils.answer(call, self.strings["out_of_range_err"], reply_markup=reply_markup)

        self.games[game_id]["bot_elo"] = int(data)
        self.set("bot_elo", int(data))
        await self._settings(call, game_id, "MARKASSUCCESS")

    async def _settings(self, call: InlineCall, game_id: str, page: str = "", param: str = "", value = None):
        reply_markup = []
        text = "✅"
        if page:
            if page == "t":
                text = "⏳"
                reply_markup.extend([
                    [
                        {"text": self.strings['blitz_text'], "action": "answer", "message": self.strings['blitz_message']}
                    ],
                    [
                        {"text": self.strings['timer'].format(3), "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'Timer', "value": 3}},
                        {"text": self.strings['timer'].format(5), "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'Timer', "value": 5}},
                    ],
                    [
                        {"text": self.strings['rapid_text'], "action": "answer", "message": self.strings['rapid_message']}
                    ],
                    [
                        {"text": self.strings['timer'].format(10), "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'Timer', "value": 10}},
                        {"text": self.strings['timer'].format(15), "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'Timer', "value": 15}},
                        {"text": self.strings['timer'].format(30), "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'Timer', "value": 30}},
                        {"text": self.strings['timer'].format(60), "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'Timer', "value": 60}}
                    ],
                    [
                        {"text": self.strings['no_clock_text'], "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'Timer', "value": True}}
                    ]
                ])
            elif page == "c":
                text = "♟️"
                reply_markup.extend([
                    [
                        {"text": self.strings['white'], "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'host_plays', "value": True}},
                        {"text": self.strings['black'], "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'host_plays', "value": False}}
                    ],
                    [
                        {"text": self.strings['random'], "callback":self._settings, "args": (game_id,), "kwargs": {"param": 'host_plays', "value": 'r'}}
                    ]
                ])
            elif page == "s":
                text = "✏️"
                reply_markup.extend([
                    [{"text": st["symbol"] + self.strings[name], "callback":self._settings, "args": (game_id,), "kwargs": {"param": "style", "value": name}}]
                    for name, st in self.styles.items()
                ])
            elif page == "e":
                text = "🧠"
                reply_markup.extend([
                    [{"text": self.strings["set_btn"], "input": self.strings["bot_elo_btn"], "handler": self._elo_validator, "args": (game_id,)}]
                ])

            reply_markup.append(
                [
                    {"text": self.strings['back'], "callback": self.settings, "args": (game_id,)}
                ]
            )

            await utils.answer(call, text, reply_markup=reply_markup, disable_security=True)
        else:
            await call.answer("✅")
            if param == "style":
                self.set("style", value)

            if param == "Timer" and isinstance(value, int):
                self.games[game_id]['Timer']['timer'] = Timer(value*60)
            else:
                self.games[game_id][param] = value
            await self.settings(call, game_id)

    def _get_settings_text(self, game_id: str):
        game = self.games[game_id]
        timer = game['Timer']
        return (
            self.strings['settings_text'].format(
                style=game['style'],

                timer=self.strings['available'] if timer['available'] and not timer['timer']
                else self.strings['timer'].format(timer['timer'].minutes()) if timer['timer']
                else self.strings['not_available'],

                color=self.strings['random'] if game['host_plays'] == 'r'
                else self.strings['white'] if game['host_plays']
                else self.strings['black']
            )
            + ("\n    " + self.strings["bot_elo"].format(elo=game["bot_elo"]) if game["vs_bot"] else "")
        )


    def _get_new_game_id(self):
        if self.games:
            past_game = next(reversed(self.games.values()))
            if not past_game.get("game", None):
                self.games.pop(past_game['game_id'], None)
        if not self.games:
            game_id = str(1)
        else:
            game_id = str(max(map(int, self.games.keys())) + 1)

        return game_id

    def _create_game(self, game_id: str, _params: dict = None):
        params = {
            "game_id": game_id,
            "vs_bot": False,
            "bot_elo": self.get("bot_elo", 3190),
            "sender": None,
            "opponent": None,
            "Timer": {
                "available": False,
                "timer": None,
                "timer_loop": False
            },
            "time": int(time.time()),
            "host_plays": "r",
            "style": self.get("style", "figures-with-circles")
        }

        if _params:
            params.update(_params)

        self.games[game_id] = GameObj(**params)


    @loader.command(ru_doc="[reply/username/id] - предложить человеку сыграть партию")
    async def chess(self, message: Message | InlineCall, _sender: dict = None):
        """[nothing/reply/username/id] - propose a person to play a game"""
        if _sender is None:
            _sender = {}
        sender, opponent = await self.get_players(message, sender=_sender)
        if not opponent:
            r_m = {"text": self.strings["i_wanna"], "callback": self.chess, "args": (sender,)}

            await utils.answer(
                message,
                self.strings["is_someone_wanna_play"],
                reply_markup=r_m,
                disable_security=True,
            )
            return 
        if sender['id'] == opponent['id'] and not self.config["play_self"]:
            await utils.answer(message, self.strings["playing_with_yourself?"])
            return

        game_id = self._get_new_game_id()

        mod_params = {
            "sender": sender,
            "opponent": opponent,
            "Timer": {
                "available": isinstance(message, Message) and isinstance(message.peer_id, PeerUser),
                "timer": None,
                "timer_loop": False
            }
        }

        self._create_game(game_id, mod_params)

        if _sender:
            self.games[game_id]["alr_accepted"] = True

        await self._invite(message, game_id)

    @loader.command(ru_doc="[reply/username/id] - предложить человеку сыграть партию против 🐟 Stockfish")
    async def stockfish(self, message: Message):
        """[reply/username/id] - propose a person to play a game against a 🐟 Stockfish"""
        if not self.config["stockfish_path"] or not check_path(self.config["stockfish_path"]):
            return await utils.answer(
                message,
                self.strings["stockfish_not_found"],
                reply_markup={
                    "text": self.strings["install_stockfish"],
                    "callback": self.install_stockfish,
                }
            )

        if message.is_reply:
            player = await self.get_players(message, opponent_only=True)
        else:
            player = await self.get_players(message, sender_only=True)

        stockfish = {
            "name": "Stockfish",
            "id": -42,
        }

        game_id = self._get_new_game_id()

        mod_params = {
            "vs_bot": True,
            "sender": stockfish,
            "opponent": player,
            "Timer": {
                "available": isinstance(message, Message) and isinstance(message.peer_id, PeerUser),
                "timer": None,
                "timer_loop": False
            }
        }

        self._create_game(game_id, mod_params)

        await self._invite(message, game_id)

    # @loader.command(ru_doc="посмотреть текущее состояние модуля и статистику своих партий")
    # async def chesstats(self, message: Message):
    #     """view the current state of the module and statistics of your games"""
    #     total_games = len(self.get("games_backup", {}))
    #     await utils.answer(message, f"♟️ <b>{self.strings['name']}</b> ♟️\n\nTotal games played: <b>{total_games}</b>")
        # TODO: добавить кнопки для просмотра состояния каждой партии; считать победы/поражения/ничьи и прочую бесполезную статистику; проверка на наличие исполняемого файла шахматного движка для возможности игры против ИИ; возможность экспорта партии в PGN; возможность продолжить сохранённую партию

    ############## Preparing all for game start... ##############

    async def _init_game(self, call: InlineCall, game_id: str, ans="yes"):
        if not await self._check_player(call, game_id=game_id, only_opponent=True): return
        if ans == "no":
            self.games.pop(game_id, None)
            await utils.answer(call, self.strings["declined"])
            return

        await utils.answer(call, "🌒")

        game = self.games[game_id]
        game["style"] = self.styles[game["style"]]

        if (turn := game.pop("host_plays")) == "r":
            turn = r.choice([True, False])

        game["sender"]["color"] = turn
        game["opponent"]["color"] = not turn
        game["Timer"].pop("available", None)
        if game.get("alr_accepted", None):
            game.pop("alr_accepted")

        await asyncio.sleep(0.8)

        if isinstance(self.games[game_id]["Timer"]["timer"], Timer):
            await utils.answer(call, self.strings["step4.T"])
            await self._set_timer(call, game_id, call._units[call.unit_id]['chat'])
            await asyncio.sleep(0.8)
            return await utils.answer(call, self.strings["waiting_for_start"])

        await self._start_game(call, game_id)

    async def _set_timer(self, board_call: InlineCall, game_id: str, chat_id):
        timer = self.games[game_id]["Timer"]["timer"]
        self.games[game_id]["Timer"]["message"] = (
            await self.inline.form(self.strings["timer_text"].format(
                int(await timer.white_time()), 
                int(await timer.black_time()), 
                ""
                ), 
                chat_id,
                reply_markup = {
                    "text": self.strings["start_timer"],
                    "callback": self._start_timer,
                    "args": (board_call, game_id,)
                },
                disable_security = True,
            )
        )

    @loader.loop(interval=1, autostart=True)
    async def main_loop(self):
        for game_id in self.games:
            if not self.games[game_id].get("backup", False) and self.games[game_id]["Timer"]["timer_loop"] and not self.games[game_id]["Timer"]["timer_is_set"]:
                async def timer_loop(game_id):
                    game = self.games[game_id]["game"]
                    timer = self.games[game_id]["Timer"]
                    timer_c = self.games[game_id]["Timer"]["timer"]

                    await timer_c.start()
                    timer["timer_is_set"] = True
                    while timer["timer_loop"]:
                        if not all([await timer_c.white_time(), await timer_c.black_time()]):
                            timer["timer_loop"] = False
                            self.the_end(game_id, "time_is_up")
                        elif game["state"] == "the_end":
                            timer["timer_loop"] = False
   
                        loser, winner = self._get_loser_and_winner(game_id)

                        await timer["message"].edit(self.strings["timer_text"].format(
                            int(await timer_c.white_time()),
                            int(await timer_c.black_time()),
                            "" if game["state"] != "the_end"
                               else "⏹️ " + self.strings[game["add_params"]["reason_of_ending"]].format(
                                      loser, winner
                               )
                            ),
                        )
                        await asyncio.sleep(1)
                    await timer.stop()
                asyncio.create_task(timer_loop(game_id))

            if self.games[game_id].get("game", None):
                if not self.games[game_id].get("backup", False):
                    self.games[game_id]["game"]["message"].inline_manager._units[
                        self.games[game_id]["game"]["message"].unit_id
                    ]["disable_security"] = True
                    self.games[game_id]["game"]["message"].inline_manager._custom_map.get(
                        self.games[game_id]["game"]["message"].unit_id, {}
                    )["disable_security"] = True # для ругающегося на эту строку гпт - по неизвестно какой причине фреймворк в какое-то время попросту
                                             # забывает про отключение его проверки. мне это нужно, чтобы сам модуль брал на себя ответсвенность
                                             # проверки, кто может управлять доской, а до кого очередь ещё не дошла
                                             # FIXME: оно, похоже, всё ещё забывает про always_allow, патч не помогает... нужно выйти на эту ошибку и посмотреть, прочему права пропадают
                
        games_backup = {}
        if time.time() - self._last_backup >= 10:
            for game_id, game in self.games.items():
                if game.get("game", None):
                    game_copy = game
                    if not game.get("backup", None):
                        game_copy = {}
                        game_copy["backup"] = True

                        game_copy["game"] = {
                            k: v for k, v in game["game"].items()
                            if k not in ("message", "root_node", "curr_node", "board", "bot")
                        }
                        game_copy["game"]["node"] = str(game["game"]["root_node"])

                        if game.get("Timer", None) and game["Timer"].get("timer", None):
                            game_copy["Timer"] = game["Timer"]["timer"].backup()

                        for key, value in game.items():
                            if key not in ("game", "Timer"):
                                game_copy[key] = value

                    games_backup[game_id] = game_copy

            self.set("games_backup", games_backup)
            self._last_backup = time.time()

    ############## Starting game... ##############

    async def _start_timer(self, call: InlineCall, board_call: InlineCall, game_id: str):
        if not await self._check_player(call, game_id): return
        timer = self.games[game_id]["Timer"]
        timer["timer_loop"] = True
        await self._start_game(board_call, game_id)

    async def _init_bot(self, game_id: str, params: dict):
        if not self.games[game_id]["vs_bot"]: return

        engine = chess.engine.SimpleEngine.popen_uci(self.config["stockfish_path"])
        engine.configure({"UCI_LimitStrength": True, "UCI_Elo": params["elo"]})

        self.games[game_id]["game"]["bot"] = engine

    async def _start_game(self, call: InlineCall, game_id: str):
        if not await self._check_player(call, game_id): return
        game = self.games[game_id]
        node = chess.pgn.Game()
        pgn = copy.deepcopy(self.pgn)
        pgn["Date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        pgn["Round"] = str(game_id)
        pgn["White"] = game["sender"]["name"] if game["sender"]["color"] else game["opponent"]["name"]
        pgn["Black"] = game["opponent"]["name"] if game["sender"]["color"] else game["sender"]["name"]
        pgn["Result"] = "*"
        node.headers.update(pgn)
        game["game"] = Game(
            board = chess.Board(),
            message = call,
            root_node = node,
            curr_node = node,
            state = "idle",
            add_params =  GameParams(
                chosen_figure_coord = "",
                reason_of_ending = "",
                promotion_move = "",
                winner_color = None,
                resigner_color = None,
                draw_offerer = None,
            ),
            bot = None,
        )
        await self._init_bot(game_id, {"elo": game["bot_elo"]})
        await self.update_board(game_id)

    def idle(self, game_id: str):
        game = self.games[game_id]["game"]
        game["state"] = "idle"
        game["add_params"]["chosen_figure_coord"] = ""
        game["add_params"]["promotion_move"] = ""
        game["add_params"]["draw_offerer"] = None

    def choose(self, game_id: str, coord: str):
        game = self.games[game_id]["game"]
        game["state"] = "in_choose"
        game["add_params"]["chosen_figure_coord"] = coord
        game["add_params"]["promotion_move"] = ""

    def promotion(self, game_id: str, move: str):
        game = self.games[game_id]["game"]
        game["state"] = "in_promotion"
        game["add_params"]["chosen_figure_coord"] = ""
        game["add_params"]["promotion_move"] = move

    def the_end(self, game_id: str, reason: str, winner: bool = None):
        game = self.games[game_id]["game"]
        game["state"] = "the_end"
        game["add_params"]["reason_of_ending"] = reason
        game["add_params"]["winner_color"] = winner
        game["add_params"]["chosen_figure_coord"] = ""
        game["add_params"]["promotion_move"] = ""
        game["root_node"].headers["Result"] = (
            "1-0" if winner is True else
            "0-1" if winner is False else
            "1/2-1/2"
        )
        if self.games[game_id]["vs_bot"]:
            game["bot"].quit()

    def _get_loser_and_winner(self, game_id: str) -> tuple[str, str]:
        game = self.games[game_id]
        if game["sender"]["color"] == self.games[game_id]["game"]["add_params"]["winner_color"]:
            return (game["opponent"]["name"], game["sender"]["name"])
        else:
            return (game["sender"]["name"], game["opponent"]["name"])

    def _get_piece_symbol(self, game_id: str, coord: str) -> str:
        game = self.games[game_id]
        piece = game["game"]["board"].piece_at(chess.parse_square(coord))
        return game["style"][piece.symbol()] if piece else " "

    def _get_move_symbol(self, game_id: str, move: str) -> str:
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

    def _get_available_moves(self, game_id: str, coord: str) -> list[str]:
        if not coord: return []
        game = self.games[game_id]
        coord = chess.parse_square(coord)
        moves = [move.uci() for move in game["game"]["board"].legal_moves if move.from_square == coord]
        return moves

    def _get_board_dict(self, game_id: str) -> dict[str, str]:
        game = self.games[game_id]
        coords = copy.deepcopy(self.coords)
        for coord in self.coords:
            coords[coord] = self._get_piece_symbol(game_id, coord)

        if game["game"]["state"] == "in_choose":
            choosen_coord = game["game"]["add_params"]["chosen_figure_coord"]
            for move in self._get_available_moves(game_id, choosen_coord):
                coord = move[2:4]
                coords[coord] = self._get_move_symbol(game_id, move)

        return coords

    def _get_reply_markup(self, game_id: str, promotion: bool = False, resign_confirm: bool = False, draw_confirm: bool = False) -> list[list[dict]]:
        game = self.games[game_id]
        is_end = game["game"]["state"] == "the_end"

        reply_markup = utils.chunks(
            [
                {
                    "text": figure,
                    "callback": self.choose_coord,
                    "args": (game_id, coord),
                }
                for coord, figure in self._get_board_dict(game_id).items()
            ][::-1],
            8
        )

        if promotion:
            reply_markup.append(
                [{"text": "⬇️↻⬇️", "action": "answer", "message": self.strings["choose_promotion"]}]
            )
            reply_markup.append(
                [
                    {
                        "text": game["style"].get(piece, piece),
                        "callback": self.pawn_promotion,
                        "args": (game_id, piece),
                    } for piece in "qrnb"
                ]
            )
        elif resign_confirm:
            reply_markup.extend(
                [
                    [
                        {
                            "text": self.strings["resign_check"],
                            "data": "_there_is_nothing",
                        }
                    ],
                    [
                        {
                            "text": self.strings["resign_yes"],
                            "callback": self.resign,
                            "args": (game_id, True),
                        },
                        {
                            "text": self.strings["resign_no"],
                            "callback": self._back_to_game,
                            "args": (game_id,),
                        },
                    ]
                ]
            )
        elif draw_confirm:
            reply_markup.extend(
                [
                    [
                        {
                            "text": self.strings["draw_offer"].format(
                                self.strings["white"] if game["game"]["add_params"]["draw_offerer"]
                                else self.strings["black"]
                            ),
                            "data": "_there_is_nothing",
                        }
                    ],
                    [
                        {
                            "text": self.strings["draw_yes"],
                            "callback": self.draw,
                            "args": (game_id, True),
                        },
                        {
                            "text": self.strings["resign_no"],
                            "callback": self._back_to_game,
                            "args": (game_id,),
                        },
                    ]
                ]
            )
        elif not is_end:
            resign = [
                {
                    "text": "🏳️",
                    "callback": self.resign,
                    "args": (game_id,),
                },
            ]

            if not game["vs_bot"]:
                resign.append(
                    {
                        "text": "🤝",
                        "callback": self.draw,
                        "args": (game_id,),
                    }
                )
            reply_markup.append(resign)
        return reply_markup

    async def update_board(self, game_id: str, promotion: bool = False, resign_confirm: bool = False, draw_confirm: bool = False):
        game = self.games[game_id]
        is_end = game["game"]["state"] == "the_end"
        reason_of_ending = game["game"]["add_params"]["reason_of_ending"]
        status = (
            self.strings["check"] if game["game"]["board"].is_check() and not is_end
            else self.strings[reason_of_ending] + "\n"
        )
        loser, winner = self._get_loser_and_winner(game_id)

        reply_markup = self._get_reply_markup(game_id, promotion, resign_confirm, draw_confirm)

        pgn = game["game"]["root_node"].accept(chess.pgn.StringExporter(columns=None, headers=False)).replace("*", "").rsplit(maxsplit=1)
        if pgn:
            pgn[-1] = f"<b>{pgn[-1]}</b>"
        else:
            pgn = ["<b>|</b>"]
        last_moves = " ".join(pgn)

        res = False

        while not res:
            res = await game["game"]["message"].edit(
                self.strings["board"].format(
                    game_id,
                    utils.escape_html(game["sender"]["name"] if game["sender"]["color"] else game["opponent"]["name"]),
                    utils.escape_html(game["opponent"]["name"] if game["sender"]["color"] else game["sender"]["name"]),
                    self.strings["white"] if game["game"]["board"].turn else self.strings["black"],
                    status.format(loser=utils.escape_html(loser), winner=utils.escape_html(winner)),
                    last_moves[-32:],
                ),
                reply_markup=reply_markup,
            )
            await asyncio.sleep(0.3)

        if game["vs_bot"] and game["game"]["board"].turn == game["sender"]["color"] and game["game"]["state"] == "idle":
            await self._bot_process_board(game_id)

    async def _bot_process_board(self, game_id: str):
        if not (game := self.games[game_id])["vs_bot"]:
            return

        board = game["game"]["board"]
        bot = game["game"]["bot"]

        _d = game["bot_elo"] // 100 - 10
        depth = r.randint(_d, _d + 15)

        result = bot.play(board, limit=chess.engine.Limit(time=0.1, depth=depth))
        move = result.move
        from_coord = chess.square_name(result.move.from_square)
        to_coord = chess.square_name(result.move.to_square)
        #logger.info(f"move: {move}, from: {from_coord}, to: {to_coord}")

        await asyncio.sleep(r.randint(1, 3))
        await self.choose_coord(None, game_id, from_coord)
        await asyncio.sleep(0.7)
        await self.choose_coord(None, game_id, to_coord)

        if move.promotion:
            await asyncio.sleep(0.7)
            await self.pawn_promotion(None, game_id, chess.piece_symbol(move.promotion))

    def make_move(self, game_id: str, move: str):
        game = self.games[game_id]["game"]
        move = chess.Move.from_uci(move)
        game["board"].push(move)
        game["curr_node"] = game["curr_node"].add_variation(move)

    async def pawn_promotion(self, call: InlineCall, game_id: str, piece: str):
        if not await self._check_player(call, game_id): return
        game = self.games[game_id]["game"]
        move = game["add_params"]["promotion_move"] + piece

        self.make_move(game_id, move)
        self.set_game_state(game_id)

        return await self.update_board(game_id)

    async def _back_to_game(self, _, game_id: str):
        self.set_game_state(game_id)
        await self.update_board(game_id)

    async def resign(self, call: InlineCall, game_id: str, confirm: bool = False):
        if not await self._check_player(call, game_id, skip_turn_check=True): return
        game = self.games[game_id]
        if not confirm:
            game["game"]["add_params"]["resigner_color"] = self._get_color_by_player(
                game_id,
                call.from_user.id
            )
            return await self.update_board(game_id, resign_confirm=True)
        
        resigner = self._get_player_by_color(
            game_id, game["game"]["add_params"]["resigner_color"]
        )

        if call.from_user.id != resigner["id"]:
            return await call.answer(self.strings["resign_not_you"])

        self.the_end(game_id, "resign", winner=not resigner["color"])
        await self.update_board(game_id)

    async def draw(self, call: InlineCall, game_id: str, accept: bool = False):
        if not await self._check_player(call, game_id, skip_turn_check=True): return
        game = self.games[game_id]
        if accept:
            offerer = self._get_player_by_color(
                game_id,
                game["game"]["add_params"]["draw_offerer"]
            )

            if call.from_user.id == offerer["id"]:
                await call.answer(self.strings["draw_not_you"])
                return
            self.the_end(game_id, "draw")
            return await self.update_board(game_id)

        game["game"]["add_params"]["draw_offerer"] = self._get_color_by_player(
            game_id,
            call.from_user.id
        )
        return await self.update_board(game_id, draw_confirm=True)

    def set_game_state(self, game_id: str):
        game = self.games[game_id]["game"]
        board = game["board"]
        self.idle(game_id)
        if board.is_checkmate():
            self.the_end(game_id, "checkmate", winner=not board.turn)
        elif board.is_stalemate():
            self.the_end(game_id, "stalemate")
        elif board.is_insufficient_material():
            self.the_end(game_id, "insufficient_material")
        elif board.is_seventyfive_moves():
            self.the_end(game_id, "seventyfive_moves")
        elif board.is_fivefold_repetition():
            self.the_end(game_id, "fivefold_repetition")

    async def choose_coord(self, call: BotInlineCall, game_id: str, coord: str):
        if not await self._check_player(call, game_id): return
        game = self.games[game_id]["game"]
        state = game["state"]

        if state == "idle":
            if self._get_available_moves(game_id, coord):
                self.choose(game_id, coord)
            else:
                await call.answer(self.strings["no_moves"])
            return await self.update_board(game_id)

        elif state == "in_choose":
            if coord == game["add_params"]["chosen_figure_coord"]: # клик по той же фигуре
                self.idle(game_id)
                return await self.update_board(game_id)

            av_moves = self._get_available_moves(game_id, game["add_params"]["chosen_figure_coord"])
            coord_matches = [move for move in av_moves if coord in move]

            if len(coord_matches) == 1: # прост ход
                self.make_move(game_id, coord_matches[0])
                self.set_game_state(game_id)
                return await self.update_board(game_id)

            elif len(coord_matches) > 1: # пешка дошла до конца
                move = coord_matches[0][:4]
                self.promotion(game_id, move)
                return await self.update_board(game_id, promotion=True)

            elif game["board"].piece_at(chess.parse_square(coord)): # другая фигура
                self.choose(game_id, coord)
                return await self.update_board(game_id)

            else: # в принципе нет там фигур
                self.idle(game_id)
                return await self.update_board(game_id)

        elif state == "in_promotion":
            return await call.answer(self.strings["can_not_move"])

        elif state == "the_end":
            return await call.answer(self.strings["game_ended"])

        else:
            await call.answer("ты игру сломал?")
            self.idle(game_id)
            return await self.update_board(game_id)



    def _get_player_by_color(self, game_id: str, color: bool):
        game = self.games[game_id]
        return game["sender"] if game["sender"]["color"] == color else game["opponent"]

    def _get_color_by_player(self, game_id: str, player_id: int):
        game = self.games[game_id]
        if game["sender"]["id"] == player_id:
            return game["sender"]["color"]
        elif game["opponent"]["id"] == player_id:
            return game["opponent"]["color"]
        return None
