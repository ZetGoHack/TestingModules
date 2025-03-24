__version__ = ("1","0","0")
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



@loader.tds
class Chess(loader.Module):
    """Шахматы для игры вдвоём."""
    strings = {
        "name": "Chess"
    }
    #####Переменные#####

    async def client_ready(self):
        self.board = {}
        self.symbols = {
    "r": "♜", "n": "♞", "b": "♝", "q": "𝗾", "k": "♚", "p": "♟", "R": "♖", "N": "♘", "B": "♗", "Q": "𝗤", "K": "♔", "P": "♙",
        }
        # self.symbolsL = {
        #     "r": "𝗿", "n": "𝗻", "b": "𝗯", "q": "𝗾", "k": "𝗸", "p": "𝗽",
        #     "R": "𝗥", "N": "𝗡", "B": "𝗕", "Q": "𝗤", "K": "𝗞", "P": "𝗣",
        # } будто кто-то будет за буквы играть...
        self.chsn = False
        self.saymyname = (await self.client.get_me()).first_name
        self.reverse = False

    def purgeSelf(self):
        self.board = {}
        self.chsn = False
        self.reverse = False
        self.Board = None
        self.you_play = None
        self.you_n_me = []
        self.places = []
        self.message = None
        self.opp_id = None
        self.opp_name = None
        self.checkmate = False
        self.stalemate = False

    #####Переменные#####


    #####Игра#####

    @loader.command() 
    async def chess(self, message):
        """[reply/username/id] предложить человеку сыграть партию в чате"""
        if self.board:
            await message.edit("Партия уже где-то запущена. Завершите или сбросьте её с <code>purgegame</code>")
            return
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
        if self.opp_id == self.message.sender_id:
            await message.edit("Одиночные шахматы? Простите, нет.")
            return
        self.you_n_me = [self.opp_id, self.message.sender_id]
        await self.inline.form(message = message, text = f"<a href='tg://user?id={self.opp_id}'>{self.opp_name}</a>, вас пригласили сыграть партию шахмат, примите?", reply_markup = [[
                {"text": "Принимаю", "callback": self.ans, "args":("y",)},
                {"text": "Нет", "callback": self.ans, "args":("n",)}],
                [{"text": "ВАЖНО","action":"answer","show_alert":True,"message":"В игре показаны фигуры в виде ASCII символов, но на тёмном фоне(база для кнопок ботов) фигуры едва различимы(как ♕♛ например).\n\nДля удобства различия они были заменены на Q(бел) и q(чёрн)",}
            ]], disable_security = True, on_unload=self.outdated()
        )
    @loader.command() 
    async def purgeGame(self, message):
        """Грубо завершить партию, очистив ВСЕ связанные с ней данные"""
        self.purgeSelf()
        await message.edit("Данные очищены")

    async def ans(self, call, data):
        if call.from_user.id == self.message.sender_id:
            await call.answer("Дай человеку ответить!")
            return
        if call.from_user.id not in self.you_n_me:
            await call.answer("Не тебе предлагают ж")
            return
        if data == 'y':
            self.Board = chess.Board()
            
            await call.edit(text="Выбираю стороны...")
            await asyncio.sleep(0.5)
            self.you_play = self.ranColor()
            text = self.sttxt()
            await call.edit(text="Готово. Загрузка доски")
            await asyncio.sleep(0.5)
            await self.LoadBoard(text, call)
        else:
            await call.edit(text="Отклонено.")

    #####Игра#####


    #####Доска#####

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

        #await self.client.send_message(self.message.chat_id, f"запуск доски без точек. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")

        await call.edit(text = text,
            reply_markup = btns[::-1],
            disable_security = True
        )

    async def UpdBoard(self, call):
        for row in range(1,9):
            rows = []
            for col in "ABCDEFGH":
                coord = f"{col}{row}"
                if any(place[-2:] == coord.lower() for place in self.places):
                        self.board[coord] = "✖" if (move := next((chess.Move.from_uci(p) for p in self.places if p[-2:] == coord.lower()), None)) and self.Board.is_capture(move) else "●"
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
        #await self.client.send_message(self.message.chat_id, f"создали кнопки. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")

        await call.edit(text = text,
            reply_markup = btns[::-1],
            disable_security = True
        )


    #####Доска#####


    #####Ходы#####

    async def clicks_handle(self, call, coord):
        if call.from_user.id not in self.you_n_me:
            await call.answer("Партия не ваша")
            return
        current_player = self.message.sender_id if (self.you_play == "w") ^ self.reverse else self.opp_id
        if call.from_user.id != current_player:
            await call.answer("Кыш от моих фигур")
            return
        if self.checkmate or self.stalemate:
            await call.answer("Партия окончена. Доступных ходов нет.")
            
        if self.chsn == False:
            #await self.client.send_message(self.message.chat_id, f"не выбрано. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
            await self.checkMove(call,coord)
        else:
            #if self.reverse:
            #await self.client.send_message(self.message.chat_id, f"выбрано. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
            matching_place = next((place for place in self.places if place[-2:] == coord.lower()), None)
            if matching_place:
                #await self.client.send_message(self.message.chat_id, f"совпадение. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
                self.Board.push(chess.Move.from_uci(matching_place))
                self.reverse = not self.reverse
                self.chsn = False
                #await call.answer("потом")
            else:
                #await self.client.send_message(self.message.chat_id, f"не совпадение. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
                prev_place = next((place for place in self.places if place[:-2] == coord.lower()), None)
                text = self.sttxt()
                if prev_place:
                    self.chsn = False
                    self.places = []
                    await self.LoadBoard(text,call)
                    return
                if not await self.checkMove(call,coord):
                    #await self.client.send_message(self.message.chat_id, f"неправильный ход сосо(сброс данных). self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
                    self.chsn = False
                    self.places = []
                    await self.LoadBoard(text,call)
                    return
                else:
                    return
                # else:
                #     await self.checkMove(call,coord)
            text = self.sttxt()
            await self.LoadBoard(text,call)
            #else:

    async def checkMove(self,call,coord):
        if self.Board.piece_at(chess.parse_square(coord.lower())):
            square = chess.parse_square(coord.lower())
            moves = [move for move in self.Board.legal_moves if move.from_square == square]
            self.places = [p for p in [move.uci() for move in moves]]
            if not self.places:
                await call.answer("Для этой фигуры нет ходов!")
                #await self.client.send_message(self.message.chat_id, f"для фигуры нет ходов. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
                return None
        else:
            await call.answer("Тут нет фигуры")
            self.places = []
            self.chsn = False
            #await self.client.send_message(self.message.chat_id, f"нема фигуры тут. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
            return None
        
        self.chsn = True
        ##await self.client.send_message(self.message.chat_id, f"Прошли проверку, вывод. self.chsn={self.chsn},coord={coord.lower()},self.reverse{self.reverse},self.places={self.places if hasattr(self,'places') else None}")
        await call.answer(f"Ставлю {self.places}")
        await self.UpdBoard(call)
        return True

    def sttxt(self):
        check = False
        self.checkmate = False
        self.stalemate = False
        self.fifty = False
        if self.Board.is_checkmate():
            self.checkmate = True
        elif self.Board.is_check():
            check = True
        elif self.Board.is_stalemate():
            self.stalemate = True
        elif self.Board.can_claim_fifty_moves():
            board.outcome()
            self.fifty = True
        if not self.checkmate and not check and not self.stalemate:
            if self.reverse:
                if self.you_play == "w":
                    return f"♔ Белые - {self.saymyname}\n👉 ♚ Чёрные - {self.opp_name} (ваш ход)\n\nw - белые фигуры, \nb - чёрные фигуры."
                else:
                    return f"♔ Белые - {self.opp_name}\n👉 ♚ Чёрные - {self.saymyname} (ваш ход)\n\nw - белые фигуры, \nb - чёрные фигуры."
            else:
                if self.you_play == "w":
                    return f"👉 ♔ Белые - {self.saymyname} (ваш ход)\n♚ Чёрные - {self.opp_name}\n\nw - белые фигуры, \nb - чёрные фигуры."
                else:
                    return f"👉 ♔ Белые - {self.opp_name} (ваш ход)\n♚ Чёрные - {self.saymyname}\n\nw - белые фигуры, \nb - чёрные фигуры."
        elif self.checkmate:
            if self.reverse:
                if self.you_play == "w":
                    return f"♔ Белые - {self.saymyname}\n♚ Чёрные - {self.opp_name}\nШах и мат! Победил(а) {self.saymyname}"
                else:
                    return f"♔ Белые - {self.opp_name}\n♚ Чёрные - {self.saymyname}\nШах и мат! Победил(а) {self.opp_name}"
            else:
                if self.you_play == "w":
                    return f"♔ Белые - {self.saymyname} \n♚ Чёрные - {self.opp_name}\nШах и мат! Победил(а) {self.opp_name}"
                else:
                    return f"♔ Белые - {self.opp_name} \n♚ Чёрные - {self.saymyname}\nШах и мат! Победил(а) {self.saymyname}"
        elif check:
            if self.reverse:
                if self.you_play == "w":
                    return f"♔ Белые - {self.saymyname}\n👉 ♚ Чёрные - {self.opp_name}\nШах!\n\nw - белые фигуры, \nb - чёрные фигуры."
                else:
                    return f"♔ Белые - {self.opp_name}\n👉 ♚ Чёрные - {self.saymyname}\nШах!\n\nw - белые фигуры, \nb - чёрные фигуры."
            else:
                if self.you_play == "w":
                    return f"👉 ♔ Белые - {self.saymyname} \n♚ Чёрные - {self.opp_name}\nШах!\n\nw - белые фигуры, \nb - чёрные фигуры."
                else:
                    return f"👉 ♔ Белые - {self.opp_name} \n♚ Чёрные - {self.saymyname}\nШах!\n\nw - белые фигуры, \nb - чёрные фигуры."
        elif self.stalemate:
            if self.reverse:
                if self.you_play == "w":
                    return f"♔ Белые - {self.saymyname}\n♚ Чёрные - {self.opp_name}\nПат. Ничья"
                else:
                    return f"♔ Белые - {self.opp_name}\n♚ Чёрные - {self.saymyname}\nПат. Ничья"
            else:
                if self.you_play == "w":
                    return f"♔ Белые - {self.saymyname} \n♚ Чёрные - {self.opp_name}\nПат. Ничья"
                else:
                    return f"♔ Белые - {self.opp_name} \n♚ Чёрные - {self.saymyname}\nПат. Ничья"
        elif self.fifty:
            if self.reverse:
                if self.you_play == "w":
                    return f"♔ Белые - {self.saymyname}\n♚ Чёрные - {self.opp_name}\nПравило 50 ходов. ничья"
                else:
                    return f"♔ Белые - {self.opp_name}\n♚ Чёрные - {self.saymyname}\nПравило 50 ходов. ничья"
            else:
                if self.you_play == "w":
                    return f"♔ Белые - {self.saymyname} \n♚ Чёрные - {self.opp_name}\nПравило 50 ходов. ничья"
                else:
                    return f"♔ Белые - {self.opp_name} \n♚ Чёрные - {self.saymyname}\nПравило 50 ходов. ничья"


    #####Ходы#####


    ##########
    async def outdated(self):
        self.purgeSelf()
        return


    def ranColor(self):
        return "w" if random.randint(1,2) == 1 else "b"
    ##########
