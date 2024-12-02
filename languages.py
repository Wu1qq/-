LANGUAGES = {
    'zh': {
        'name': '中文',
        'welcome': """
👋 欢迎使用客服机器人！

🔰 基本功能：
• 创建私密聊天室
• 支持多媒体消息
• 24小时自动清理
• 安全且匿名
...
        """,
        'room_created': """
🎉 聊天室创建成功！

📋 房间信息：
• ID: {room_id}
• 创建时间: {created_time}
...
        """,
        # ... 其他消息
    },
    'en': {
        'name': 'English',
        'welcome': """
👋 Welcome to Customer Service Bot!

🔰 Basic Features:
• Create private chat rooms
• Support multimedia messages
• 24-hour auto cleanup
• Safe and anonymous
...
        """,
        'room_created': """
🎉 Chat Room Created!

📋 Room Info:
• ID: {room_id}
• Created at: {created_time}
...
        """,
        # ... other messages
    }
}

DEFAULT_LANGUAGE = 'zh'

def get_text(key, lang=DEFAULT_LANGUAGE, **kwargs):
    """获取指定语言的文本"""
    try:
        text = LANGUAGES[lang][key]
        return text.format(**kwargs) if kwargs else text
    except KeyError:
        # 如果找不到对应语言或文本，返回默认语言
        return LANGUAGES[DEFAULT_LANGUAGE][key].format(**kwargs) if kwargs else LANGUAGES[DEFAULT_LANGUAGE][key] 