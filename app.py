from pyscript import document, ffi
import math
import time

EMPTY = ""
HUMAN = "X"
AI = "O"
current_turn = "X"
game_over = False
board = [EMPTY] * 9

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]

MOVE_ORDER = [4, 0, 2, 6, 8, 1, 3, 5, 7]
PROXIES = []


def el(element_id):
    return document.getElementById(element_id)


def set_status(message):
    el("status").innerText = message


def set_stat(element_id, value):
    el(element_id).innerText = str(value)


def reset_stats():
    set_stat("stat-algo", "-")
    set_stat("stat-depth", "-")
    set_stat("stat-nodes", "-")
    set_stat("stat-pruned", "-")
    set_stat("stat-maxdepth", "-")
    set_stat("stat-time", "-")
    set_stat("stat-score", "-")


def available_moves(state):
    return [i for i in MOVE_ORDER if state[i] == EMPTY]


def check_winner(state, player):
    return any(all(state[i] == player for i in line) for line in WIN_LINES)


def get_winning_line(state, player):
    for line in WIN_LINES:
        if all(state[i] == player for i in line):
            return line
    return None


def is_draw(state):
    return EMPTY not in state and not check_winner(state, HUMAN) and not check_winner(state, AI)


def terminal_score(state, depth):
    if check_winner(state, AI):
        return 100 - depth
    if check_winner(state, HUMAN):
        return -100 + depth
    return 0


def heuristic_score(state):
    if check_winner(state, AI) or check_winner(state, HUMAN) or is_draw(state):
        return terminal_score(state, 0)

    ai_open = 0
    human_open = 0

    for line in WIN_LINES:
        cells = [state[i] for i in line]
        if HUMAN not in cells:
            ai_open += 1
        if AI not in cells:
            human_open += 1

    center_bonus = 1 if state[4] == AI else 0
    center_penalty = 1 if state[4] == HUMAN else 0

    return (ai_open - human_open) + center_bonus - center_penalty


def minimax(state, depth, depth_limit, maximizing, stats):
    stats["nodes"] += 1
    stats["max_depth"] = max(stats["max_depth"], depth)

    if check_winner(state, AI) or check_winner(state, HUMAN) or is_draw(state):
        return terminal_score(state, depth), None

    if depth == depth_limit:
        return heuristic_score(state), None

    best_move = None

    if maximizing:
        best_score = -math.inf
        for move in available_moves(state):
            state[move] = AI
            score, _ = minimax(state, depth + 1, depth_limit, False, stats)
            state[move] = EMPTY

            if score > best_score:
                best_score = score
                best_move = move

        return best_score, best_move

    best_score = math.inf
    for move in available_moves(state):
        state[move] = HUMAN
        score, _ = minimax(state, depth + 1, depth_limit, True, stats)
        state[move] = EMPTY

        if score < best_score:
            best_score = score
            best_move = move

    return best_score, best_move


def alphabeta(state, depth, depth_limit, alpha, beta, maximizing, stats):
    stats["nodes"] += 1
    stats["max_depth"] = max(stats["max_depth"], depth)

    if check_winner(state, AI) or check_winner(state, HUMAN) or is_draw(state):
        return terminal_score(state, depth), None

    if depth == depth_limit:
        return heuristic_score(state), None

    best_move = None

    if maximizing:
        best_score = -math.inf
        for move in available_moves(state):
            state[move] = AI
            score, _ = alphabeta(state, depth + 1, depth_limit, alpha, beta, False, stats)
            state[move] = EMPTY

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)
            if beta <= alpha:
                stats["pruned"] += 1
                break

        return best_score, best_move

    best_score = math.inf
    for move in available_moves(state):
        state[move] = HUMAN
        score, _ = alphabeta(state, depth + 1, depth_limit, alpha, beta, True, stats)
        state[move] = EMPTY

        if score < best_score:
            best_score = score
            best_move = move

        beta = min(beta, best_score)
        if beta <= alpha:
            stats["pruned"] += 1
            break

    return best_score, best_move


def update_stats(algorithm, depth_limit, score, stats, elapsed_ms):
    algo_name = "Minimax" if algorithm == "minimax" else "Alpha-Beta"
    set_stat("stat-algo", algo_name)
    set_stat("stat-depth", depth_limit)
    set_stat("stat-nodes", stats["nodes"])
    set_stat("stat-pruned", stats["pruned"] if algorithm == "alphabeta" else 0)
    set_stat("stat-maxdepth", stats["max_depth"])
    set_stat("stat-time", f"{elapsed_ms:.3f} ms")
    set_stat("stat-score", score)


def finish_game(winner=None):
    global game_over
    game_over = True
    render()

    if winner == HUMAN:
        set_status(f"Anda menang! ({HUMAN})")
    elif winner == AI:
        set_status(f"AI menang! ({AI})")
    else:
        set_status("Hasil permainan seri.")


def render():
    winning = get_winning_line(board, HUMAN) or get_winning_line(board, AI)

    for i in range(9):
        button = el(f"cell-{i}")
        value = board[i]
        button.innerText = value

        class_names = ["cell"]
        if value == "X":
            class_names.append("filled-x")
        elif value == "O":
            class_names.append("filled-o")

        if winning and i in winning:
            class_names.append("winner")

        button.className = " ".join(class_names)
        button.disabled = bool(value) or game_over or (current_turn != HUMAN)

    if not game_over:
        if current_turn == HUMAN:
            set_status(f"Giliran Anda ({HUMAN})")
        else:
            set_status(f"Giliran AI ({AI})")


def ai_move():
    global current_turn

    if game_over:
        return

    depth_limit = int(el("depth").value)
    algorithm = el("algorithm").value

    stats = {"nodes": 0, "max_depth": 0, "pruned": 0}
    start = time.perf_counter()

    if algorithm == "minimax":
        score, move = minimax(board, 0, depth_limit, True, stats)
    else:
        score, move = alphabeta(board, 0, depth_limit, -math.inf, math.inf, True, stats)

    elapsed_ms = (time.perf_counter() - start) * 1000
    update_stats(algorithm, depth_limit, score, stats, elapsed_ms)

    if move is None:
        finish_game(None)
        return

    board[move] = AI

    if check_winner(board, AI):
        finish_game(AI)
        return

    if is_draw(board):
        finish_game(None)
        return

    current_turn = HUMAN
    render()


def handle_cell_click(event):
    global current_turn

    if game_over or current_turn != HUMAN:
        return

    index = int(event.currentTarget.dataset.index)

    if board[index] != EMPTY:
        return

    board[index] = HUMAN
    render()

    if check_winner(board, HUMAN):
        finish_game(HUMAN)
        return

    if is_draw(board):
        finish_game(None)
        return

    current_turn = AI
    render()
    ai_move()


def start_new_game(event=None):
    global HUMAN, AI, current_turn, game_over, board

    HUMAN = el("player-symbol").value
    AI = "O" if HUMAN == "X" else "X"

    board = [EMPTY] * 9
    game_over = False
    current_turn = "X"
    reset_stats()
    render()

    if current_turn == AI:
        ai_move()


def bind_events():
    cell_proxy = ffi.create_proxy(handle_cell_click)
    PROXIES.append(cell_proxy)

    for i in range(9):
        el(f"cell-{i}").addEventListener("click", cell_proxy)

    new_game_proxy = ffi.create_proxy(start_new_game)
    PROXIES.append(new_game_proxy)
    el("new-game").addEventListener("click", new_game_proxy)


bind_events()
start_new_game()