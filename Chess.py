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
from .. import loader, utils
import asyncio, random

def ranColor():
    return "w" if random.randint(1,2) == 1 else "b"

def flip_board(board):
    flipped_board = {}
    for pos, piece in board.items():
        col, row = pos[0], pos[1]
        new_row = str(9 - int(row))
        flipped_board[col + new_row] = piece
    return flipped_board

@loader.tds
class Chess(loader.Module):
    """Chesssssssss s s ss ss"""
    strings = {
        "name": "Chess"
    }
    async def client_ready(self):
        self.board = {
        "A1":"♖","B1":"♘","C1":"♗","D1":"♕","E1":"♔","F1":"♗","G1":"♘","H1":"♖",
        "A2":"♙","B2":"♙","C2":"♙","D2":"♙","E2":"♙","F2":"♙","G2":"♙","H2":"♙",
        "A3":" ","B3":" ","C3":" ","D3":" ","E3":" ","F3":" ","G3":" ","H3":" ",
        "A4":" ","B4":" ","C4":" ","D4":" ","E4":" ","F4":" ","G4":" ","H4":" ",
        "A5":" ","B5":" ","C5":" ","D5":" ","E5":" ","F5":" ","G5":" ","H5":" ",
        "A6":" ","B6":" ","C6":" ","D6":" ","E6":" ","F6":" ","G6":" ","H6":" ",
        "A7":"♟","B7":"♟","C7":"♟","D7":"♟","E7":"♟","F7":"♟","G7":"♟","H7":"♟",
        "A8":"♜","B8":"♞","C8":"♝","D8":"♛","E8":"♚","F8":"♝","G8":"♞","H8":"♜",
        }

    async def clicks_handle(self, call):
        #await self.message.respond(f"@{str(call.from_user.username)} щас ток это реализовано")
        pass
    async def playing(self, u):
        pass
    async def offer_outdated(self, call):
        await call.edit("Время на ответ истекло.")
        return

    async def ans(self, call, data):
        if call.from_user.id == self.message.sender_id:
            await call.answer("Дай человеку ответить!")
            return
        if data == 'y':
            await call.edit(text="УРА!!!!1!1!! Щааа")
            await asyncio.sleep(0.5)
            await call.edit(text="Во")
            await asyncio.sleep(0.5)
            await self.UpdBoard("Это начальная позиция шахмат. \nХод белых", call)
            you_play = ranColor()
            await self.playing(you_play)
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
            opp_name = opponent.first_name
        else:
            args = utils.get_args(message)
            if len(args)==0:
                message.edit("Вы не указали с кем играть")
                return
            opponent = args[0]
            try:
                if opponent.isdigit():
                    self.opp_id = int(opponent)
                    opponent = await self.client.get_entity(self.opp_id)
                    opp_name = opponent.first_name
                else:
                    opponent = await self.client.get_entity(opponent)
                    opp_name = opponent.first_name
                    self.opp_id = opponent.id
            except:
                await message.edit("Я не нахожу такого пользователя")
                return
                
        await self.inline.form(message = message, text = f"<a href='tg://openmessage?user_id={self.opp_id}'>{opp_name}</a>, тя в игру пригласили, примешь?", reply_markup = [
                {"text": "КОНЕЧНО ТЫ ЧО", "callback": self.ans, "args":("y",)},
                {"text": "ни", "callback": self.ans, "args":("n",)},
            ], always_allow=[self.opp_id], ttl=60, on_unload=self.offer_outdated
        )
    async def UpdBoard(self, text, call):
        btns = []
        for row in range(1,9):
            rows = []
            for col in "ABCDEFGH":
                coord = f"{col}{row}"
                rows.append({"text": f"{self.board[f'{col}{row}']}", "callback": self.clicks_handle, "args":(coord,)})
            btns.append(rows)

        
        await call.edit(text = text,
            reply_markup = btns,
            always_allow=[self.opp_id]
        )
