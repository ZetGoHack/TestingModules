#чесс нуда
from .. import loader
@loader.tds
class Chess(loader.Module):
    """Chesssssssss s s ss ss"""
    strings = {
        "name": "Chess"
    }
    async def yea(self, call):
        await m.respond(f"@{str(call.from_user.username)}")

    async def ans(self, call, data):
        if data == 'y':
            await call.edit(text="УРА")
        else:
            await call.edit(text="(")
    
    board = {
    "A1":"♖","B1":"♘","C1":"♗","D1":"♕","E1":"♔","F1":"♗","G1":"♘","H1":"♖",
    "A2":"♙","B2":"♙","C2":"♙","D2":"♙","E2":"♙","F2":"♙","G2":"♙","H2":"♙",
    "A3":" ","B3":" ","C3":" ","D3":" ","E3":" ","F3":" ","G3":" ","H3":" ",
    "A4":" ","B4":" ","C4":" ","D4":" ","E4":" ","F4":" ","G4":" ","H4":" ",
    "A5":" ","B5":" ","C5":" ","D5":" ","E5":" ","F5":" ","G5":" ","H5":" ",
    "A6":" ","B6":" ","C6":" ","D6":" ","E6":" ","F6":" ","G6":" ","H6":" ",
    "A7":"♟","B7":"♟","C7":"♟","D7":"♟","E7":"♟","F7":"♟","G7":"♟","H7":"♟",
    "A8":"♜","B8":"♞","C8":"♝","D8":"♛","E8":"♚","F8":"♝","G8":"♞","H8":"♜",
    }
    @loader.command() 
    async def chess(self, message):
        await self.inline.form(message = message, text = "Тя в игру пригласили, примешь?", reply_markup = [
                {"text": "КОНЕЧНО ТЫ ЧО", "callback": self.ans, "args":("y",)},
                {"text": "ни", "callback": self.ans, "args":("n",)},
            ]
        )
    async def board(self):
        await self.inline.form(message = message, text = "‌", reply_markup = 
            [
                [
                    {"text": f"{board['A1']}", "callback": yea},
                    {"text": f"{board['B1']}", "callback": yea},
                    {"text": f"{board['C1']}", "callback": yea},
                    {"text": f"{board['D1']}", "callback": yea},
                    {"text": f"{board['E1']}", "callback": yea},
                    {"text": f"{board['F1']}", "callback": yea},
                    {"text": f"{board['G1']}", "callback": yea},
                    {"text": f"{board['H1']}", "callback": yea}
                ],
                [
                    {"text": f"{board['A2']}", "callback": yea},
                    {"text": f"{board['B2']}", "callback": yea},
                    {"text": f"{board['C2']}", "callback": yea},
                    {"text": f"{board['D2']}", "callback": yea},
                    {"text": f"{board['E2']}", "callback": yea},
                    {"text": f"{board['F2']}", "callback": yea},
                    {"text": f"{board['G2']}", "callback": yea},
                    {"text": f"{board['H2']}", "callback": yea}
                ],
                [
                    {"text": f"{board['A3']}", "callback": yea},
                    {"text": f"{board['B3']}", "callback": yea},
                    {"text": f"{board['C3']}", "callback": yea},
                    {"text": f"{board['D3']}", "callback": yea},
                    {"text": f"{board['E3']}", "callback": yea},
                    {"text": f"{board['F3']}", "callback": yea},
                    {"text": f"{board['G3']}", "callback": yea},
                    {"text": f"{board['H3']}", "callback": yea}
                ],
                [
                    {"text": f"{board['A4']}", "callback": yea},
                    {"text": f"{board['B4']}", "callback": yea},
                    {"text": f"{board['C4']}", "callback": yea},
                    {"text": f"{board['D4']}", "callback": yea},
                    {"text": f"{board['E4']}", "callback": yea},
                    {"text": f"{board['F4']}", "callback": yea},
                    {"text": f"{board['G4']}", "callback": yea},
                    {"text": f"{board['H4']}", "callback": yea}
                ],
                [
                    {"text": f"{board['A5']}", "callback": yea},
                    {"text": f"{board['B5']}", "callback": yea},
                    {"text": f"{board['C5']}", "callback": yea},
                    {"text": f"{board['D5']}", "callback": yea},
                    {"text": f"{board['E5']}", "callback": yea},
                    {"text": f"{board['F5']}", "callback": yea},
                    {"text": f"{board['G5']}", "callback": yea},
                    {"text": f"{board['H5']}", "callback": yea}
                ],
                [
                    {"text": f"{board['A6']}", "callback": yea},
                    {"text": f"{board['B6']}", "callback": yea},
                    {"text": f"{board['C6']}", "callback": yea},
                    {"text": f"{board['D6']}", "callback": yea},
                    {"text": f"{board['E6']}", "callback": yea},
                    {"text": f"{board['F6']}", "callback": yea},
                    {"text": f"{board['G6']}", "callback": yea},
                    {"text": f"{board['H6']}", "callback": yea}
                ],
                [
                    {"text": f"{board['A7']}", "callback": yea},
                    {"text": f"{board['B7']}", "callback": yea},
                    {"text": f"{board['C7']}", "callback": yea},
                    {"text": f"{board['D7']}", "callback": yea},
                    {"text": f"{board['E7']}", "callback": yea},
                    {"text": f"{board['F7']}", "callback": yea},
                    {"text": f"{board['G7']}", "callback": yea},
                    {"text": f"{board['H7']}", "callback": yea}
                ],
                [
                    {"text": f"{board['A8']}", "callback": yea},
                    {"text": f"{board['B8']}", "callback": yea},
                    {"text": f"{board['C8']}", "callback": yea},
                    {"text": f"{board['D8']}", "callback": yea},
                    {"text": f"{board['E8']}", "callback": yea},
                    {"text": f"{board['F8']}", "callback": yea},
                    {"text": f"{board['G8']}", "callback": yea},
                    {"text": f"{board['H8']}", "callback": yea}
                ]
            ]
        )
