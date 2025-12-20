from ..tl_cache import CustomTelegramClient
from herokutl.tl import functions as f
from herokutl.tl import types as t
from herokutl.tl import custom as cstm
from .. import loader, utils
c = CustomTelegramClient()

async def content():
 #.e
 folder = 11

 gifts = [
   t.InputSavedStarGiftUser(g.msg_id)
   async for g in c.get_saved_gifts(
    "me",
    folder,
    )
  ]
 
 def by_caption(i: cstm.StarGift):
  return i.message.text.lower() if i.message else ""
 
 gifts.sort(key=by_caption)
 
 await c(f.payments.UpdateStarGiftCollectionRequest("me", folder, order=gifts))
