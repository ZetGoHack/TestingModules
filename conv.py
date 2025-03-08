from .. import loader, utils
import asyncio
@loader.tds
class Test(loader.Module):
    """A"""
    strings = {"name": "Conv"}
    @loader.command()
    async def conv(self):
        """B"""
        async with self._client.conversation(7212151458) as conv:
            await conv.send_message("сюда")
            try:
                r = await conv.get_response()
            except:
                pass
            await conv.send_message(r)
    
