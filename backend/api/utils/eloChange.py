# backend/api/utils/eloChange.py

def calculate_new_elo_pair_after_draw(black_elo, white_elo, k=32):
    expected_black = 1 / (1 + 10 ** ((white_elo - black_elo) / 400))
    expected_white = 1 / (1 + 10 ** ((black_elo - white_elo) / 400))

    new_black_elo = black_elo + k * (0.5 - expected_black)
    new_white_elo = white_elo + k * (0.5 - expected_white)

    return round(new_black_elo), round(new_white_elo)

def calculate_new_elo_pair_after_win(black_elo, white_elo, black_wins, k=32):
    expected_black = 1 / (1 + 10 ** ((white_elo - black_elo) / 400))
    expected_white = 1 / (1 + 10 ** ((black_elo - white_elo) / 400))

    if black_wins:
        new_black_elo = black_elo + k * (1 - expected_black)
        new_white_elo = white_elo + k * (0 - expected_white)
    else:
        new_black_elo = black_elo + k * (0 - expected_black)
        new_white_elo = white_elo + k * (1 - expected_white)

    return round(new_black_elo), round(new_white_elo)