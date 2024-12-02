# Telegram 客服机器人

一个功能强大的 Telegram 客服机器人，支持创建临时聊天室、多媒体消息、自动回复等功能。

## 功能特点

### 基础功能
- 创建私密聊天室
- 24小时自动清理
- 支持多媒体消息
- 聊天室密码保护
- 二维码/链接分享

### 消息支持
- 文字消息
- 图片（支持说明文字）
- 视频
- 文件
- 语音消息
- 贴纸
- GIF动图

### 管理功能
- 用户管理（禁言/解禁）
- 消息管理（撤回/编辑）
- 聊天室公告
- 消息置顶
- 自动回复规则
- 消息模板

### 高级功能
- 多语言支持
- 消息转发
- 聊天记录搜索
- 聊天记录导出
- 投票功能
- 定时消息
- 用户活跃度统计

## 系统要求

- Python 3.7+
- Linux/macOS/Windows
- 1GB+ RAM
- 1GB+ 存储空间
- 稳定的网络连接

## 安装步骤

1. 克隆仓库
bash
git clone https://github.com/Wu1qq/telegram-service-bot.git

cd telegram-service-bot

2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 创建必要目录

```bash
mkdir media qr_codes logs
```

5. 配置机器人
- 复制 `config.py.example` 到 `config.py`
- 在 `config.py` 中设置您的 Bot Token 和其他配置

## 配置说明

### 基本配置

```python
# config.py
BOT_TOKEN = "YOUR_BOT_TOKEN"
BOT_USERNAME = "your_bot_username"

# 聊天室配置
MAX_ROOMS_PER_USER = 3
ROOM_EXPIRE_HOURS = 24
MAX_USERS_PER_ROOM = 50
```

### 媒体文件配置

```python
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_FILE_TYPES = {
    'image': ['image/jpeg', 'image/png', 'image/gif'],
    'video': ['video/mp4', 'video/mpeg'],
    'document': ['application/pdf', 'application/msword', 'text/plain'],
    'audio': ['audio/mpeg', 'audio/ogg']
}
```

## 使用说明

### 基本命令
- `/start` - 启动机器人
- `/new_chat` - 创建新的聊天室
- `/help` - 显示帮助信息
- `/leave` - 退出当前聊天室

### 管理命令
- `/close` - 关闭聊天室（仅创建者）
- `/mute` - 禁言用户
- `/unmute` - 解除禁言
- `/ban` - 封禁用户（全局管理员）
- `/unban` - 解封用户（全局管理员）

### 高级功能
- `/forward` - 转发消息
- `/search` - 搜索聊天记录
- `/export` - 导出聊天记录
- `/poll` - 创建投票
- `/schedule` - 设置定时消息

## 项目结构

```
telegram-service-bot/
├── bot.py              # 主程序
├── config.py           # 配置文件
├── chat_room.py        # 聊天室类
├── message_handler.py  # 消息处理器
├── user_manager.py     # 用户管理器
├── languages.py        # 多语言支持
├── requirements.txt    # 依赖列表
├── media/             # 媒体文件目录
├── qr_codes/          # 二维码存储目录
└── logs/              # 日志目录
```

## 部署说明

### 使用 systemd（Linux）

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

服务配置示例：

```ini
[Unit]
Description=Telegram Service Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/telegram_service_bot
Environment=PATH=/path/to/telegram_service_bot/venv/bin
ExecStart=/path/to/telegram_service_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

## 维护说明

### 日志查看

```bash
tail -f logs/bot.log
```

### 备份数据

```bash
./backup_script.sh
```

### 更新步骤
1. 停止服务
2. 备份数据
3. 更新代码
4. 更新依赖
5. 启动服务

## 故障排除

### 常见问题
1. 机器人无响应
   - 检查网络连接
   - 检查 Bot Token
   - 查看错误日志

2. 媒体文件上传失败
   - 检查文件大小限制
   - 检查存储空间
   - 检查文件权限

3. 内存使用过高
   - 检查并清理过期文件
   - 调整最大用户数限制
   - 优化媒体文件处理

## 安全建议

1. 定期更新系统和依赖
2. 设置适当的文件权限
3. 启用防火墙
4. 定期备份数据
5. 监控系统资源使用

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 作者：记忆匪浅
- Email：a3361150770@gmail.com

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基本聊天功能
- 多媒体支持
- 用户管理

### v1.1.0 (2024-01-15)
- 添加多语言支持
- 添加自动回复功能
- 添加消息模板功能
- 优化性能

## 致谢

感谢以下开源项目：
- python-telegram-bot
- Pillow
- python-magic
```



