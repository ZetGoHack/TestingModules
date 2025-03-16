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
        self.board = {}
        self.symbols = {
    "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟", "r": "♖", "n": "♘", "b": "♗", "q": "♕", "k": "♔", "p": "♙",
}
        self.chsn = False
        self.saymyname = (await self.client.get_me()).first_name
        self.reverse = False

    async def checkMove(self,call,coord):
        if self.Board.piece_at(chess.parse_square(coord.lower())):
            square = chess.parse_square(coord.lower())
            moves = [move for move in self.Board.legal_moves if move.from_square == square]
            self.places = [p for p in [move.uci() for move in moves]]
            if not self.places:
                await call.answer("Для этой фигуры нет ходов!")
                await self.client.send_message(self.message.chat_id, f"для фигуры нет ходов. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
                return None
        else:
            await call.answer("Тут нет фигуры")
            await self.client.send_message(self.message.chat_id, f"нема фигуры тут. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
            return None
        
        self.chsn = True
        await self.client.send_message(self.message.chat_id, f"Прошли проверку, вывод. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
        await call.answer(f"Ставлю {self.places}")
        await self.UpdBoard(call)

    def sttxt(self):
        if self.reverse:
            if self.you_play == "w":
                return f"♚ Белые - {self.saymyname}\n♔ Чёрные - {self.opp_name} (ваш ход)"
            else:
                return f"♚ Белые - {self.opp_name}\n♔ Чёрные - {self.saymyname} (ваш ход)"
        else:
            if self.you_play == "w":
                return f"♚ Белые - {self.saymyname} (ваш ход)\n♔ Чёрные - {self.opp_name}"
            else:
                return f"♚ Белые - {self.opp_name} (ваш ход)\n♔ Чёрные - {self.saymyname}"

    async def clicks_handle(self, call, coord):
        if call.from_user.id not in self.you_n_me:
            await call.answer("Партия не ваша")
            return
        if self.chsn == False:
            await self.client.send_message(self.message.chat_id, f"не выбрано. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
            await self.checkMove(call,coord)
        else:
            #if self.reverse:
            await self.client.send_message(self.message.chat_id, f"выбрано. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
            matching_place = next((place for place in self.places if place[-2:] == coord.lower()), None)
            if matching_place:
                await self.client.send_message(self.message.chat_id, f"совпадение. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
                self.Board.push(chess.Move.from_uci(matching_place))
                #await call.answer("потом")
            else:
                await self.client.send_message(self.message.chat_id, f"не совпадение. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
                if not await self.checkMove(call,coord):
                    await self.client.send_message(self.message.chat_id, f"неправильный ход сосо(сброс данных). self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
                    self.chsn == False
                    self.places = []
                    await self.LoadBoard(text,call)
                # else:
                #     await self.checkMove(call,coord)
            text = self.sttxt()
            self.reverse = not self.reverse
            self.chsn = False
            await self.LoadBoard(text,call)
            #else:
                
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
            self.Board = chess.Board()
            await call.edit(text="УРА!!!!1!1!! Щааа")
            await asyncio.sleep(0.5)
            self.you_play = ranColor()
            text = self.sttxt()
            await call.edit(text="Во")
            await asyncio.sleep(0.5)
            await self.LoadBoard(text, call)
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
                    self.opp_name = opponent.first_name
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
    async def LoadBoard(self, text, call):
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

        await self.client.send_message(self.message.chat_id, f"запуск доски без точек. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
        if self.reverse:
            await call.edit(text = text,
                reply_markup = btns,
                disable_security = True
            )
        else:
            await call.edit(text = text,
                reply_markup = btns[::-1],
                disable_security = True
            )

    async def UpdBoard(self, call):
        #board = str(self.Board).split("\n")
        for row in range(1,9):
            rows = []
            for col in "ABCDEFGH":
                coord = f"{col}{row}"
                if any(place[-2:] == coord.lower() for place in self.places):
                        self.board[coord] = "•"
                else:
                    piece = self.Board.piece_at(chess.parse_square(coord.lower()))
                    self.board[coord] =  self.symbols[piece.symbol()] if piece else " "
                
                
        text = self.sttxt()  
        btns = []
        for row in range(1,9):
            rows = []
            for col in "ABCDEFGH":
                coord = f"{col}{row}"
                rows.append({"text": f"{self.board[f'{col}{row}']}", "callback": self.clicks_handle, "args":(coord,)})
            btns.append(rows)
        await self.client.send_message(self.message.chat_id, f"создали кнопки. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
        if self.reverse:
            await call.edit(text = text,
                reply_markup = btns,
                disable_security = True
            )
        else:
            await call.edit(text = text,
                reply_markup = btns[::-1],
                disable_security = True
            )
