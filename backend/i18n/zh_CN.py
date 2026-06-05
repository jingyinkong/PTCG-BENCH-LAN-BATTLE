"""Simplified Chinese translations for backend messages."""

MESSAGES: dict[str, str] = {
    # Auth
    "username_length": "用户名长度须为 3-20 个字符",
    "username_chars": "用户名只能包含字母、数字和下划线",
    "password_length": "密码长度须至少 6 个字符",
    "auth_no_token": "未提供认证 token",
    "auth_bad_format": "认证格式错误",
    "auth_invalid_token": "token 无效或已过期",
    "auth_username_taken": "用户名已存在",
    "auth_wrong_credentials": "用户名或密码错误",

    # Game rooms
    "room_not_found": "房间不存在",
    "room_unjoinable": "房间已无法加入",
    "room_own": "不能加入自己创建的房间",
    "room_full": "房间已满",
    "room_not_host": "只有房主可以开始对战",
    "room_waiting": "等待对手加入",
    "room_need_decks": "双方都需要选择卡组",
    "room_game_started": "对战开始",
    "room_not_in_room": "你不在这个房间中",

    # WebSocket / Game
    "game_invalid_json": "无效的 JSON 格式",
    "game_not_found": "游戏不存在",
    "game_not_your_turn": "不是你的回合",
    "game_invalid_action": "无效的操作索引",
    "coin_not_your_call": "不是由你猜硬币",
    "coin_invalid_choice": "请选择 heads 或 tails",
    "coin_not_your_choose": "不是由你选择先/后攻",
    "coin_invalid_choose": "请选择 first 或 second",
    "opponent_disconnected": "对手已断开连接",
    "opponent_timeout": "对手断线超时",
    "opponent_left_game": "对手已退出游戏",
    "message_bad_format": "消息格式错误",
    "message_missing_action_index": "缺少 action_index 字段",
    "message_action_index_int": "action_index 必须是整数",
}
