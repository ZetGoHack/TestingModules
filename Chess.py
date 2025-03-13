#чесс нуда

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
import asyncio


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
    async def yea(self, call):
        await self.message.respond(f"@{str(call.from_user.username)} щас ток это реализовано")
        
    async def offer_outdated(self, call):
        await call.edit("Время на ответ истекло.")
        return

    async def ans(self, call, data):
        if data == 'y':
            await call.edit(text="УРА!!!!1!1!! Щааа")
            await asyncio.sleep(1.5)
            await call.edit(text="Во")
            await asyncio.sleep(0.5)
            await self.UpdBoard("Это начальная позиция шахмат. Я хз как чёрных реализовать", call)
        else:
            await call.edit(text="(")
    
    
    @loader.command() 
    async def chess(self, message):
        """[reply/username/id] предложить человеку сыграть партию"""
        self.message = message
        if message.is_reply:
            r = await message.get_reply_message()
            opponent = r.sender
            opp_id = opponent.id
            opp_name = opponent.first_name
        else:
            args = utils.get_args(message)
            if len(args)==0:
                message.edit("Вы не указали с кем играть")
                return
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
                await message.edit("Я не нахожу такого пользователя")
                
        await self.inline.form(message = message, text = "<a href='tg://openmessage?user_id={opp_id}'>{opp_name}</a>, тя в игру пригласили, примешь?", reply_markup = [
                {"text": "КОНЕЧНО ТЫ ЧО", "callback": self.ans, "args":("y",)},
                {"text": "ни", "callback": self.ans, "args":("n",)},
            ], always_allow=[opp_id], ttl=60, on_unload=offer_outdated
        )
    async def UpdBoard(self, text, call):
        await call.edit(text = text, reply_markup = 
            [
                [
                    {"text": f"{self.board['A1']}", "callback": self.yea},
                    {"text": f"{self.board['B1']}", "callback": self.yea},
                    {"text": f"{self.board['C1']}", "callback": self.yea},
                    {"text": f"{self.board['D1']}", "callback": self.yea},
                    {"text": f"{self.board['E1']}", "callback": self.yea},
                    {"text": f"{self.board['F1']}", "callback": self.yea},
                    {"text": f"{self.board['G1']}", "callback": self.yea},
                    {"text": f"{self.board['H1']}", "callback": self.yea}
                ],
                [
                    {"text": f"{self.board['A2']}", "callback": self.yea},
                    {"text": f"{self.board['B2']}", "callback": self.yea},
                    {"text": f"{self.board['C2']}", "callback": self.yea},
                    {"text": f"{self.board['D2']}", "callback": self.yea},
                    {"text": f"{self.board['E2']}", "callback": self.yea},
                    {"text": f"{self.board['F2']}", "callback": self.yea},
                    {"text": f"{self.board['G2']}", "callback": self.yea},
                    {"text": f"{self.board['H2']}", "callback": self.yea}
                ],
                [
                    {"text": f"{self.board['A3']}", "callback": self.yea},
                    {"text": f"{self.board['B3']}", "callback": self.yea},
                    {"text": f"{self.board['C3']}", "callback": self.yea},
                    {"text": f"{self.board['D3']}", "callback": self.yea},
                    {"text": f"{self.board['E3']}", "callback": self.yea},
                    {"text": f"{self.board['F3']}", "callback": self.yea},
                    {"text": f"{self.board['G3']}", "callback": self.yea},
                    {"text": f"{self.board['H3']}", "callback": self.yea}
                ],
                [
                    {"text": f"{self.board['A4']}", "callback": self.yea},
                    {"text": f"{self.board['B4']}", "callback": self.yea},
                    {"text": f"{self.board['C4']}", "callback": self.yea},
                    {"text": f"{self.board['D4']}", "callback": self.yea},
                    {"text": f"{self.board['E4']}", "callback": self.yea},
                    {"text": f"{self.board['F4']}", "callback": self.yea},
                    {"text": f"{self.board['G4']}", "callback": self.yea},
                    {"text": f"{self.board['H4']}", "callback": self.yea}
                ],
                [
                    {"text": f"{self.board['A5']}", "callback": self.yea},
                    {"text": f"{self.board['B5']}", "callback": self.yea},
                    {"text": f"{self.board['C5']}", "callback": self.yea},
                    {"text": f"{self.board['D5']}", "callback": self.yea},
                    {"text": f"{self.board['E5']}", "callback": self.yea},
                    {"text": f"{self.board['F5']}", "callback": self.yea},
                    {"text": f"{self.board['G5']}", "callback": self.yea},
                    {"text": f"{self.board['H5']}", "callback": self.yea}
                ],
                [
                    {"text": f"{self.board['A6']}", "callback": self.yea},
                    {"text": f"{self.board['B6']}", "callback": self.yea},
                    {"text": f"{self.board['C6']}", "callback": self.yea},
                    {"text": f"{self.board['D6']}", "callback": self.yea},
                    {"text": f"{self.board['E6']}", "callback": self.yea},
                    {"text": f"{self.board['F6']}", "callback": self.yea},
                    {"text": f"{self.board['G6']}", "callback": self.yea},
                    {"text": f"{self.board['H6']}", "callback": self.yea}
                ],
                [
                    {"text": f"{self.board['A7']}", "callback": self.yea},
                    {"text": f"{self.board['B7']}", "callback": self.yea},
                    {"text": f"{self.board['C7']}", "callback": self.yea},
                    {"text": f"{self.board['D7']}", "callback": self.yea},
                    {"text": f"{self.board['E7']}", "callback": self.yea},
                    {"text": f"{self.board['F7']}", "callback": self.yea},
                    {"text": f"{self.board['G7']}", "callback": self.yea},
                    {"text": f"{self.board['H7']}", "callback": self.yea}
                ],
                [
                    {"text": f"{self.board['A8']}", "callback": self.yea},
                    {"text": f"{self.board['B8']}", "callback": self.yea},
                    {"text": f"{self.board['C8']}", "callback": self.yea},
                    {"text": f"{self.board['D8']}", "callback": self.yea},
                    {"text": f"{self.board['E8']}", "callback": self.yea},
                    {"text": f"{self.board['F8']}", "callback": self.yea},
                    {"text": f"{self.board['G8']}", "callback": self.yea},
                    {"text": f"{self.board['H8']}", "callback": self.yea}
                ]
            ]
        )
