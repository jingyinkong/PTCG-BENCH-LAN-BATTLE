"""English translations for backend messages."""

MESSAGES: dict[str, str] = {
    # Auth
    "username_length": "Username must be 3–20 characters",
    "username_chars": "Username may only contain letters, digits, and underscores",
    "password_length": "Password must be at least 6 characters",
    "auth_no_token": "Authentication token not provided",
    "auth_bad_format": "Invalid authentication format",
    "auth_invalid_token": "Token is invalid or expired",
    "auth_username_taken": "Username already exists",
    "auth_wrong_credentials": "Incorrect username or password",

    # Game rooms
    "room_not_found": "Room not found",
    "room_unjoinable": "Room is no longer joinable",
    "room_own": "Cannot join your own room",
    "room_full": "Room is full",
    "room_not_host": "Only the host can start the game",
    "room_waiting": "Waiting for opponent to join",
    "room_need_decks": "Both players need to choose a deck",
    "room_game_started": "Game started",
    "room_not_in_room": "You are not in this room",

    # WebSocket / Game
    "game_invalid_json": "Invalid JSON format",
    "game_not_found": "Game not found",
    "game_not_your_turn": "Not your turn",
    "game_invalid_action": "Invalid action index",
    "coin_not_your_call": "Not your turn to call the coin toss",
    "coin_invalid_choice": "Please choose heads or tails",
    "coin_not_your_choose": "Not your turn to choose first/second",
    "coin_invalid_choose": "Please choose first or second",
    "opponent_disconnected": "Opponent disconnected",
    "opponent_timeout": "Opponent timed out",
    "opponent_left_game": "Opponent left the game",
    "message_bad_format": "Invalid message format",
    "message_missing_action_index": "Missing action_index field",
    "message_action_index_int": "action_index must be an integer",
}
