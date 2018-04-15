import chess.pgn
from . import models


def encode_move(move):
    if move.promotion:
        byte1 = move.from_square + 64
        byte2 = move.to_square + 64 * (move.promotion - 2)
    else:
        byte1 = move.from_square
        byte2 = move.to_square

    return bytes([byte1, byte2])


def decode_move(move):
    if move[0] > 64:
        return chess.Move(move[0] % 64, move[1] % 64, (move[1] // 64) + 2)
    else:
        return chess.Move(move[0], move[1])


def encode_moves(game):
    res = bytearray()
    for move in game.main_line():
        res.extend(encode_move(move))

    return bytes(res)


def parse_pgn_name_header(name):
    if "," in name:
        i = name.index(",")
        lastname = name[:i].strip()
        firstname = name[i+1:].strip()
        return [firstname,lastname]
    else:
        return ["", name]


def load_game(game, owner):
    white = parse_pgn_name_header(game.headers["White"])
    black = parse_pgn_name_header(game.headers["Black"])

    obj = models.Object(owner=owner)
    obj.save()
    g = models.Game(
        object=obj,
        moves=encode_moves(game),
        white=models.find_or_add_player(white[0], white[1], owner),
        black=models.find_or_add_player(black[0], black[1], owner),
        result=game.headers["Result"]
    )
    g.save()
    return g


def load_file(file, owner):
    pgn = open(file)
    while True:
        game = chess.pgn.read_game(pgn)
        if not game:
            break
        load_game(game, account)
