import traceback
try:
    from core.engine import Board, Ship
    board = Board(size=6, ships=[Ship("P1", 2, [("A",1), ("B",1)])], ship_sizes=[2])
    board.receive_shot("C2")
    print("Minimal:", board.grid_text_minimal())
    board.receive_shot("A1")
    print("Minimal:", board.grid_text_minimal())
    print("Funciona.")
except Exception as e:
    traceback.print_exc()
