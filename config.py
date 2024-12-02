# 机器人配置
BOT_TOKEN = "YOUR_BOT_TOKEN"
BOT_USERNAME = "your_bot_username"

# 聊天室配置
MAX_ROOMS_PER_USER = 3  # 每个用户最多可创建的聊天室数量
ROOM_EXPIRE_HOURS = 24  # 聊天室过期时间（小时）
MAX_USERS_PER_ROOM = 50  # 每个聊天室的最大用户数
MAX_MESSAGE_LENGTH = 4096  # 最大消息长度

# 媒体文件配置
MAX_FILE_SIZE = 20 * 1024 * 1024  # 最大文件大小（20MB）
ALLOWED_FILE_TYPES = {
    'image': ['image/jpeg', 'image/png', 'image/gif'],
    'video': ['video/mp4', 'video/mpeg'],
    'document': ['application/pdf', 'application/msword', 'text/plain'],
    'audio': ['audio/mpeg', 'audio/ogg']
}

# 路径配置
MEDIA_DIR = "media"
QR_CODES_DIR = "qr_codes"

# 清理配置
CLEANUP_INTERVAL = 30  # 清理间隔（分钟）

# 欢迎信息配置
WELCOME_MESSAGE = """
👋 欢迎使用客服机器人！

🔰 基本功能：
• 创建私密聊天室
• 支持多媒体消息
• 24小时自动清理
• 安全且匿名

📝 使用方法：
1. 使用 /new_chat 创建新的聊天室
2. 分享聊天室链接或二维码给其他人
3. 开始聊天！

🛡 安全提示：
• 聊天内容24小时后自动清除
• 聊天室可设置密码保护
• 可随时关闭聊天室

❓ 需要帮助？
使用 /help 查看完整命令列表
"""

# 新聊天室创建成功消息模板
NEW_ROOM_MESSAGE = """
🎉 聊天室创建成功！

📋 房间信息：
• ID: {room_id}
• 创建时间: {created_time}
• 过期时间: {expire_time}

🔗 加入方式：
• 链接: {chat_link}
• 或扫描下方二维码

⚙️ 管理功能：
• /setpass - 设置密码
• /roominfo - 查看房间信息
• /close - 关闭聊天室

✨ 已启用的功能：
• 多媒体消息支持
• 实时消息同步
• 成员管理
• 文件分享
"""

# 加入聊天室成功消息模板
JOIN_ROOM_MESSAGE = """
✅ 成功加入聊天室！

📝 聊天室信息：
• ID: {room_id}
• 当前成员: {member_count}/{max_members}
• 剩余时间: {remaining_time}

💡 使用提示：
• 直接发送消息开始聊天
• 支持发送图片、视频等多媒体
• 使用 /leave 退出聊天室
"""

# 聊天室关闭提醒消息
ROOM_CLOSE_MESSAGE = """
⚠️ 聊天室即将关闭

📢 重要提示：
• 所有消息将被清除
• 媒体文件将被删除
• 链接将失效

感谢您的使用！
"""

# 帮助信息配置
HELP_MESSAGE = """
📋 命令列表：

基本命令：
/start - 启动机器人
/new_chat - 创建新的聊天室
/leave - 退出当前聊天室
/help - 显示此帮助信息

聊天室管理：
/close - 关闭聊天室（仅创建者）
/setpass - 设置聊天室密码
/roominfo - 查看聊天室信息
/announce - 发布/清除公告
/revoke - 撤回消息（回复要撤回的消息）

管理员命令：
/mute - 禁言用户
/unmute - 解除禁言
/ban - 封禁用户（全局管理员）
/unban - 解封用户（全局管理员）

💡 使用提示：
• 撤回消息：回复要撤回的消息并使用 /revoke
• 发布公告：/announce 公告内容
• 清除公告：/announce 不带参数

✨ 支持的消息类型：
• 文字消息
• 图片（支持说明文字）
• 视频（支持说明文字）
• 文件
• 语音消息
• 贴纸
• GIF动图

📝 高级功能：
/forward - 转发消息到其他聊天室
/search - 搜索聊天记录
/export - 导出聊天记录（仅管理员）

💡 使用说明：
• 转发消息：回复要转发的消息并使用 /forward <目标聊天室ID>
• 搜索消息：/search <关键词>
• 导出记录：/export（将生成JSON文件）

⚡️ 特殊功能：
/poll - 创建投票 (/poll 问题 选项1 选项2 ...)
/schedule - 设置定时消息 (/schedule <分钟> <消息内容>)

💡 补充说明：
• 投票：每个用户只能投一次票
• 定时消息：时间范围1-1440分钟（24小时）

📊 状态功能：
/online - 查看在线用户列表
/read - 查看消息已读状态（回复消息使用）

💡 补充说明：
• 5分钟无活动视为离线
• 消息已读状态实时更新

🌐 语言设置：
/setlang - 设置界面语言
/setwelcome - 设置自定义欢迎消息

💡 使用说明：
• 设置语言：/setlang <语言代码>
• 设置欢迎消息：/setwelcome <消息内容>

📌 消息管理：
/pin - 置顶消息（回复消息使用）
/unpin - 取消置顶（回复消息使用）
/pinned - 查看所有置顶消息
/edit - 编辑消息（回复消息并输入新内容）

💡 使用说明：
• 每个聊天室最多3条置顶消息
• 只能编辑自己的消息或管理员可编辑任何消息
• 消息编辑会通知所有成员

🤖 自动回复：
/autoreply - 添加自动回复规则 (/autoreply add <关键词> <回复内容>)
/delreply - 删除自动回复规则 (/delreply <关键词>)
/listreplies - 查看所有自动回复规则

📝 消息模板：
/template - 添加消息模板 (/template add <模板名称> <模板内容>)
/use - 使用消息模板 (/use <模板名称>)
/templates - 查看所有消息模板

💡 使用说明：
• 自动回复规则对所有成员消息生效
• 消息模板支持多行文本
• 只有管理员可以管理自动回复和模板

📊 统计功能：
/activity - 查看聊天室活动统计

💡 说明：
• 统计包含消息类型分布
• 显示用户活跃度
• 显示聊天室运行时间
"""

# 在线状态配置
ONLINE_TIMEOUT = 300  # 5分钟无活动视为离线 