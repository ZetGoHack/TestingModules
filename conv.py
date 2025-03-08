from .. import loader, utils
import asyncio
@loader.tds
class Test(loader.Module):
    """A"""
    strings = {"name": "Conv"}
    @loader.command()
    async def conv(self, msg):
        """B"""
        async with self._client.conversation(7212151458) as conv:
            await conv.send_message("сюда")
            try:
                r = await conv.get_response()
            except:
                nn = 1
                while True:
                    nn += 1
                    await msg.edit(f"nn{nn}")
                    try:
                        r = await conv.get_response()
                    except:
                        continue
                    if r:
                        break
            await conv.send_message(r)
    
