__version__ = (0,0,0)
#░░░███░███░███░███░███
#░░░░░█░█░░░░█░░█░░░█░█
#░░░░█░░███░░█░░█░█░█░█
#░░░█░░░█░░░░█░░█░█░█░█
#░░░███░███░░█░░███░███

# meta developer: @nullmod
# requires: python-chess gdown

import chess.engine
import gdown
import logging

from telethon.tl.types import (
    Message,
)

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class ChessAnalyzer(loader.Module):
    """
    Docstring for ChessAnalyzer
    """

    strings = {"name": "ChessAnalyzer"}

    def client_ready(self):
        if not self.lookup("Chess"):
            raise loader.SelfUnload(
                "You don't have a main Chess module. "
                "Analyser requires it for for better "
                "interaction with Chess module. "
                "The analyzer will (most likely) have more "
                "capabilities than just analysis :)"
            )

    @loader.command()
    async def gameslist(self, message: Message):
        games = self.lookup("Chess").games