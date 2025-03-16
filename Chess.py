#чесс нуда
__version__ = ("NOT","DONE","YET")
#░░░░░░░░░░░░░░░░░░░░░░
#░░░░░░░░░░██░░██░░░░░░
#░░░░░░░░░████████░░░░░
#░░░░░░░░░████████░░░░░
#░░░░░░░░░░██████░░░░░░
#░░░░░░░░░░░░██░░░░░░░░
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



# meta developer: @nullmod
# requires: python-chess
from .. import loader, utils
import asyncio, random, chess

def ranColor():
    return "w" if random.randint(1,2) == 1 else "b"

@loader.tds
class Chess(loader.Module):
    """Chesssssssss s s ss ss"""
    strings = {
        "name": "Chess"
    }
    async def client_ready(self):
        self.Board = chess.Board()
        self.board = {}
        self.symbols = {
    "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟", "r": "♖", "n": "♘", "b": "♗", "q": "♕", "k": "♔", "p": "♙",
}
        self.chsn = False
        self.saymyname = (await self.client.get_me()).first_name

    async def clicks_handle(self, call, coord):
        if call.from_user.id not in self.you_n_me:
            await call.answer("Партия не ваша")
            return
        if self.chsn == False:
            if self.Board.piece_at(chess.parse_square(coord.lower())):
                square = chess.parse_square(coord.lower())
                moves = [move for move in self.Board.legal_moves if move.from_square == square]
                places = [p[2:] for p in [move.uci() for move in moves]]
                if not places:
                    await call.answer("Для этой фигуры нет ходов!")
                    return
            else:
                await call.answer("Тут нет фигур")
            self.chsn = True
            await call.answer(f"Ставлю {places}")
            await self.UpdBoard(call,places)
        else:
            await call.answer("потом")
        pass
        
    async def offer_outdated(self, call):
        await self.message.respond("Время на ответ истекло")
        return

    async def ans(self, call, data):
        if call.from_user.id == self.message.sender_id:
            await call.answer("Дай человеку ответить!")
            return
        if call.from_user.id not in self.you_n_me:
            await call.answer("Не тебе предлагают ж")
            return
        if data == 'y':
            await call.edit(text="УРА!!!!1!1!! Щааа")
            await asyncio.sleep(0.5)
            you_play = ranColor()
            if you_play == "w":
                text = f"♚ Белые - {self.saymyname}\n♔ Чёрные - {self.opp_name}\nХод белых ♚"
            else:
                text = f"♚ Белые - {self.opp_name}\n♔ Чёрные - {self.saymyname}\nХод белых ♚"
            await call.edit(text="Во")
            await asyncio.sleep(0.5)
            await self.StartBoard(text, call)
        else:
            await call.edit(text="ну ладно(")


    @loader.command() 
    async def chess(self, message):
        """[reply/username/id] предложить человеку сыграть партию"""
        self.message = message
        if message.is_reply:
            r = await message.get_reply_message()
            opponent = r.sender
            self.opp_id = opponent.id
            self.opp_name = opponent.first_name
        else:
            args = utils.get_args(message)
            if len(args)==0:
                await message.edit("Вы не указали с кем играть")
                return
            opponent = args[0]
            try:
                if opponent.isdigit():
                    self.opp_id = int(opponent)
                    opponent = await self.client.get_entity(self.opp_id)
                    self.opp_name = opponent.first_name
                else:
                    opponent = await self.client.get_entity(opponent)
                    opp_name = opponent.first_name
                    self.opp_id = opponent.id
            except:
                await message.edit("Я не нахожу такого пользователя")
                return
        self.you_n_me = [self.opp_id, self.message.sender_id]
        await self.inline.form(message = message, text = f"<a href='tg://openmessage?user_id={self.opp_id}'>{self.opp_name}</a>, тя в игру пригласили, примешь?", reply_markup = [
                {"text": "КОНЕЧНО ТЫ ЧО", "callback": self.ans, "args":("y",)},
                {"text": "ни", "callback": self.ans, "args":("n",)},
            ], disable_security = True
        )
    async def StartBoard(self, text, call):
        #board = str(self.Board).split("\n")
        for row in range(1,9):
            rows = []
            for col in "ABCDEFGH":
                coord = f"{col}{row}"
                piece = self.Board.piece_at(chess.parse_square(coord.lower()))
                self.board[coord] =  self.symbols[piece.symbol()] if piece else " "
                
                
                
        btns = []
        for row in range(1,9):
            rows = []
            for col in "ABCDEFGH":
                coord = f"{col}{row}"
                rows.append({"text": f"{self.board[f'{col}{row}']}", "callback": self.clicks_handle, "args":(coord,)})
            btns.append(rows)


        await call.edit(text = text,
            reply_markup = btns[::-1],
            disable_security = True,
            always_allow=self.you_n_me
        )
    async def UpdBoard(self, call, mbplcs=None):
        #board = str(self.Board).split("\n")
        if not mbplcs:
            mbplcs = []
        for row in range(1,9):
            rows = []
            for col in "ABCDEFGH":
                coord = f"{col}{row}"
                if coord.lower() in mbplcs:
                        self.board[coord] = "•"
                else:
                    piece = self.Board.piece_at(chess.parse_square(coord.lower()))
                    self.board[coord] =  self.symbols[piece.symbol()] if piece else " "
                
                
        text = "Втоой этап"   
        btns = []
        for row in range(1,9):
            rows = []
            for col in "ABCDEFGH":
                coord = f"{col}{row}"
                rows.append({"text": f"{self.board[f'{col}{row}']}", "callback": self.clicks_handle, "args":(coord,)})
            btns.append(rows)


        await call.edit(text = text,
            reply_markup = btns[::-1],
            disable_security = True
        )
