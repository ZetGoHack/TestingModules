#чесс нуда
async def yea(call, data):
    msg = str(dir(call))
    await m.respond(f"@{str(call.from_user.username)}")
    
board = {
    A1:"",B1:"",C1:"",D1:"",E1:"",F1:"",G1:"",H1:"",
    A1:"",B1:"",C1:"",D1:"",E1:"",F1:"",G1:"",H1:"",
    A1:"",B1:"",C1:"",D1:"",E1:"",F1:"",G1:"",H1:"",
    A1:"",B1:"",C1:"",D1:"",E1:"",F1:"",G1:"",H1:"",
    A1:"",B1:"",C1:"",D1:"",E1:"",F1:"",G1:"",H1:"",
    A1:"",B1:"",C1:"",D1:"",E1:"",F1:"",G1:"",H1:"",
    A1:"",B1:"",C1:"",D1:"",E1:"",F1:"",G1:"",H1:"",
    A1:"",B1:"",C1:"",D1:"",E1:"",F1:"",G1:"",H1:"",
} 

self.inline.form(message = message, text = "‌", reply_markup = [
        [
            {"text": "♖", "callback": yea},
            {"text": "♘", "callback": yea},
            {"text": "♗", "callback": yea},
            {"text": "♕", "callback": yea},
            {"text": "♔", "callback": yea},
            {"text": "♗", "callback": yea},
            {"text": "♘", "callback": yea},
            {"text": "♖", "callback": yea}
        ],
        [
            {"text": "♙", "callback": yea},
            {"text": "♙", "callback": yea},
            {"text": "♙", "callback": yea},
            {"text": "♙", "callback": yea},
            {"text": "♙", "callback": yea},
            {"text": "♙", "callback": yea},
            {"text": "♙", "callback": yea},
            {"text": "♙", "callback": yea}
        ],
        [
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea}
        ],
        [
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea}
        ],
        [
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea}
        ],
        [
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea},
            {"text": " ", "callback": yea}
        ],
        [
            {"text": "♟", "callback": yea},
            {"text": "♟", "callback": yea},
            {"text": "♟", "callback": yea},
            {"text": "♟", "callback": yea},
            {"text": "♟", "callback": yea},
            {"text": "♟", "callback": yea},
            {"text": "♟", "callback": yea},
            {"text": "♟", "callback": yea}
        ],
        [
            {"text": "♜", "callback": yea},
            {"text": "♞", "callback": yea},
            {"text": "♝", "callback": yea},
            {"text": "♚", "callback": yea},
            {"text": "♛", "callback": yea},
            {"text": "♝", "callback": yea},
            {"text": "♞", "callback": yea},
            {"text": "♜", "callback": yea}
        ]
    ]
)
