import chess.pgn
from . import models
from datetime import datetime
from io import StringIO


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


def encode_moves_from_uci(moves):
    res = bytearray()
    for move in moves:
        res.extend(encode_move(chess.Move.from_uci(move)))
    return bytes(res)


def san_moves(moves):
    game = chess.pgn.Game()
    node = game
    res = []
    for move in moves:
        node = node.add_main_variation(move)
        res.append(node.san())
    return res


def parse_pgn_name_header(name):
    """Split a pgn name header as [firstname, lastname]."""
    if "," in name:
        i = name.index(",")
        lastname = name[:i].strip()
        firstname = name[i+1:].strip()
        return [firstname, lastname]
    else:
        return ["", name]


def load_game(game, owner):
    """Add a chess game to the database."""
    if game.headers["White"] == "?":
        white = None
    else:
        try:
            white_elo = int(game.headers["WhiteElo"])
        except (ValueError, KeyError):
            white_elo = None
        white_name = parse_pgn_name_header(game.headers["White"])
        white = models.find_or_add_player(
            white_name[0],
            white_name[1],
            owner,
            elo_rating=white_elo
        )

    if game.headers["Black"] == "?":
        black = None
    else:
        try:
            black_elo = int(game.headers["BlackElo"])
        except (ValueError, KeyError):
            black_elo = None
        black_name = parse_pgn_name_header(game.headers["Black"])
        black = models.find_or_add_player(
            black_name[0],
            black_name[1],
            owner,
            elo_rating=black_elo
        )

    if game.headers["Event"] == "?":
        event = None
    else:
        if "EventDate" in game.headers and "?" not in game.headers["EventDate"]:
            # validate date value
            try:
                datetime.strptime(game.headers["EventDate"], "%Y.%m.%d")
                # PGN uses YYYY.MM.DD, Django uses YYYY-MM-DD
                event_date = game.headers["EventDate"].replace('.', '-')
            except ValueError:
                # Replace invalid date formats with NULL
                print("Ignoring invalid date in pgn file : "
                      + game.headers["EventDate"])
                event_date = None
        else:
            event_date = None

        event = models.find_or_add_event(
            game.headers["Event"],
            owner,
            start_date=event_date
        )

    if game.headers["Site"] == "?":
        location = None
    else:
        location = game.headers["Site"]

    if "?" in game.headers["Date"]:
        # just give up if date is not complete
        date = None
    else:
        # validate date value
        try:
            datetime.strptime(game.headers["Date"], "%Y.%m.%d")
            # PGN uses YYYY.MM.DD, Django uses YYYY-MM-DD
            date = game.headers["Date"].replace('.', '-')
        except ValueError:
            # Replace invalid date formats with NULL
            print("Ignoring invalid date in pgn file : "
                  + game.headers["Date"])
            date = None

    obj = models.create_obj(owner)
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
    return g, obj


def load_file(file, owner):
    """Add games from a pgn file to the database."""
    while True:
        game = chess.pgn.read_game(file)
        if not game:
            break
        load_game(game, owner)


def load_string(str, owner):
    """Add games from a pgn string to the database."""
    pgn = StringIO(str)
    load_file(pgn, owner)
