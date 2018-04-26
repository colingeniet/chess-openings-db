import chess.pgn
from . import models


def encode_move(move):
    """Encode a chess move into two bytes."""
    if move.promotion:
        byte1 = move.from_square + 64
        byte2 = move.to_square + 64 * (move.promotion - 2)
    else:
        byte1 = move.from_square
        byte2 = move.to_square

    return bytes([byte1, byte2])


def decode_move(move):
    """Decode two bytes representing a chess move."""
    if move[0] > 64:
        return chess.Move(move[0] % 64, move[1] % 64, (move[1] // 64) + 2)
    else:
        return chess.Move(move[0], move[1])


def encode_moves(game):
    """Encode a game moves into a bytes sequence."""
    res = bytearray()
    for move in game.main_line():
        res.extend(encode_move(move))

    return bytes(res)

def decode_moves(moves):
    moves_iter = iter(moves)
    list = []
    while True:
        try:
            move = [next(moves_iter), next(moves_iter)]
        except StopIteration:
            return list

        list.append(decode_move(move))


def parse_pgn_name_header(name):
    """Split a pgn name header as [firstname, lastname]."""
    if "," in name:
        i = name.index(",")
        lastname = name[:i].strip()
        firstname = name[i+1:].strip()
        return [firstname,lastname]
    else:
        return ["", name]


def load_game(game, owner):
    """Add a chess game to the database."""
    if game.headers["White"] == "?":
        white = None
    else:
        white_name = parse_pgn_name_header(game.headers["White"])
        white = models.find_or_add_player(white_name[0], white_name[1], owner)

    if game.headers["Black"] == "?":
        black = None
    else:
        black_name = parse_pgn_name_header(game.headers["Black"])
        black = models.find_or_add_player(black_name[0], black_name[1], owner)

    if game.headers["Event"] == "?":
        event = None
    else:
        event = models.find_or_add_event(game.headers["Event"], owner)

    if game.headers["Site"] == "?":
        location = None
    else:
        location = game.headers["Site"]

    if "?" in game.headers["Date"]:
        # just give up if date is not complete
        date = None
    else:
        # PGN uses YYYY.MM.DD, SQL uses YYYY-MM-DD
        date = game.headers["Date"].replace('.','-')

    obj = models.Object(owner=owner)
    obj.save()
    g = models.Game(
        object=obj,
        moves=encode_moves(game),
        white=white,
        black=black,
        result=game.headers["Result"],
        event=event,
        location=location,
        start_date=date
    )
    g.save()
    return g


def load_file(file, owner):
    """Add games from a pgn file to the database."""
    while True:
        game = chess.pgn.read_game(file)
        if not game:
            break
        load_game(game, owner)
