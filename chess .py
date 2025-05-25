from datetime import datetime, timezone
import chess
import chess.engine
import chess.pgn

engine = chess.engine.SimpleEngine.popen_uci("../stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe")
board = chess.Board()
game = chess.pgn.Game() 
game.headers["Event"] = "test_chessengine %s" % (engine.id)
game.headers["Site"] = "http://wiki.bitplan.com/index.php/PlayChessWithAWebCam" 
game.headers["White"] = "%s" % (engine.id)
game.headers["Black"] = "%s" % (engine.id)
game.headers["Date"] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
moveIndex=0
node=None
while not board.is_game_over():
    result = engine.play(board, chess.engine.Limit(time=0.1))
    move=str(result.move)
    board.push(result.move)
    print ("%d-%s: %s" % (moveIndex//2+1,"white" if moveIndex%2==0 else "black",move))
    print (board.unicode())
    if moveIndex == 0:
        node = game.add_variation(chess.Move.from_uci(move))
    else:
        node = node.add_variation(chess.Move.from_uci(move))
    moveIndex+=1

engine.quit()    
print (game)   