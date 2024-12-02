from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import logging
import os
import qrcode
from datetime import datetime, timedelta
import uuid
from chat_room import ChatRoom
from message_handler import MessageHandler
from apscheduler.schedulers.background import BackgroundScheduler
import glob
import functools
from config import *
from user_manager import UserManager
import json
from io import BytesIO
import time
from languages import get_text, LANGUAGES

# 配置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储聊天室信息
chat_rooms = {}
user_manager = UserManager()

def handle_error(func):
    """错误处理装饰器"""
    @functools.wraps(func)
    def wrapper(update, context, *args, **kwargs):
        try:
            return func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            update.message.reply_text(
                "抱歉，发生了一些错误。请稍后重试或联系管理员。"
            )
    return wrapper

def cleanup_expired_rooms():
    """清理过期的聊天室"""
    current_time = datetime.now()
    expired_rooms = []
    
    for room_id, room in chat_rooms.items():
        if room.is_expired():
            # 通知所有用户聊天室已过期
            for user_id in room.users:
                try:
                    updater.bot.send_message(
                        chat_id=user_id,
                        text=f"聊天室 {room_id} 已过期，即将关闭！"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify user {user_id}: {e}")
            
            expired_rooms.append(room_id)
            
            # 清理媒体文件
            cleanup_media_files(room_id)
    
    # 删除过期的聊天室
    for room_id in expired_rooms:
        del chat_rooms[room_id]
        
def cleanup_media_files(room_id):
    """清理聊天室的媒体文件"""
    media_pattern = f"media/{room_id}_*"
    qr_file = f"qr_codes/{room_id}.png"
    
    # 删除媒体文件
    for file in glob.glob(media_pattern):
        try:
            os.remove(file)
        except Exception as e:
            logger.error(f"Failed to delete media file {file}: {e}")
            
    # 删除二维码件
    try:
        if os.path.exists(qr_file):
            os.remove(qr_file)
    except Exception as e:
        logger.error(f"Failed to delete QR code {qr_file}: {e}")

def cleanup_inactive_users():
    """清理离线用户"""
    for room in chat_rooms.values():
        current_time = time.time()
        inactive_users = []
        
        for user_id, last_active in room.online_users.items():
            if current_time - last_active > ONLINE_TIMEOUT:
                inactive_users.append(user_id)
                
        for user_id in inactive_users:
            del room.online_users[user_id]

@handle_error
def start(update, context):
    """启动命令处理"""
    args = context.args
    if args and args[0] in chat_rooms:
        # 加入现有聊天室
        room_id = args[0]
        room = chat_rooms[room_id]
        
        if room.is_expired():
            update.message.reply_text("该聊天室已过期！")
            return
            
        if room.is_full():
            update.message.reply_text("聊天室已满！")
            return
            
        # 检查用户是否被封禁
        if update.effective_user.id in room.banned_users:
            update.message.reply_text("您已被禁止加入该聊天室")
            return
            
        # 添加用户到聊天室
        room.add_user(update.effective_user.id)
        context.user_data['current_room'] = room_id
        
        # 发送欢迎消息
        remaining_time = room.expire_time - datetime.now()
        hours = remaining_time.total_seconds() // 3600
        
        welcome_msg = JOIN_ROOM_MESSAGE.format(
            room_id=room_id,
            member_count=len(room.users),
            max_members=room.max_users,
            remaining_time=f"{int(hours)}小时"
        )
        update.message.reply_text(welcome_msg)
        
        # 通知其他成员
        for user_id in room.users:
            if user_id != update.effective_user.id:
                context.bot.send_message(
                    chat_id=user_id,
                    text=f"新成员 {update.effective_user.first_name} 加入了聊天室"
                )
    else:
        # 发送欢迎信息
        update.message.reply_text(WELCOME_MESSAGE)

@handle_error
def new_chat(update, context):
    """创建新的聊天室"""
    user_id = update.effective_user.id
    
    # 检查用户是否可以创建新聊天室
    if not user_manager.can_create_room(user_id):
        update.message.reply_text("您已达到最大聊天室创建数量限制")
        return
        
    room_id = str(uuid.uuid4())[:8]
    chat_rooms[room_id] = ChatRoom(room_id, user_id)
    
    # 生成聊天室链接
    chat_link = f"https://t.me/{BOT_USERNAME}?start={room_id}"
    
    # 生成二维码
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(chat_link)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # 保存二维码
    qr_path = f"{QR_CODES_DIR}/{room_id}.png"
    qr_image.save(qr_path)
    
    # 准备欢迎信息
    room = chat_rooms[room_id]
    welcome_msg = NEW_ROOM_MESSAGE.format(
        room_id=room_id,
        created_time=room.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        expire_time=room.expire_time.strftime('%Y-%m-%d %H:%M:%S'),
        chat_link=chat_link
    )
    
    # 发送聊天室信息
    with open(qr_path, 'rb') as qr_file:
        update.message.reply_photo(
            photo=qr_file,
            caption=welcome_msg,
            parse_mode=ParseMode.HTML
        )

@handle_error
def help_command(update, context):
    """帮助命令"""
    help_text = """
可用命令列表：
基本命令：
/start - 启动机器人
/new_chat - 创建新的聊天室
/leave - 退出当前聊天室
/close - 关闭当前聊天室（仅创建者可用）
/help - 显示此帮助信息

聊天室管理：
/setpass - 设置聊天室密码
/roominfo - 查看聊天室信息
/mute - 禁言用户（管理员可用）
/unmute - 解除禁言（管理员可用）

管理员命令：
/ban - 封禁用户（全局管理员可用）
/unban - 解封用户（全局管理员可用）

支持的消息类型：
- 文字消息
- 图片（支持说明文字）
- 视频（支持说明文字）
- 文件
- 语音消息
- 贴纸
- GIF动图
    """
    update.message.reply_text(help_text)

def leave_chat(update, context):
    """退出聊天室"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    room.remove_user(update.effective_user.id)
    del context.user_data['current_room']
    update.message.reply_text("已退出聊天室！")

@handle_error
def close_chat(update, context):
    """关闭聊天室"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    if not room.is_creator(update.effective_user.id):
        update.message.reply_text("只有聊天室创建者才能关闭聊天室！")
        return
    
    # 通知所有用户
    for user_id in room.users:
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=ROOM_CLOSE_MESSAGE
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
    
    # 关闭聊天
    room.close_room()
    cleanup_media_files(room_id)
    del chat_rooms[room_id]
    update.message.reply_text("聊天室已关闭！")

@handle_error
def ban_user(update, context):
    """封禁用户"""
    if not user_manager.is_admin(update.effective_user.id):
        update.message.reply_text("此命令仅管理员可用！")
        return

    if not context.args:
        update.message.reply_text("请提供要封禁的用户ID")
        return

    try:
        user_id = int(context.args[0])
        user_manager.ban_user(user_id)
        update.message.reply_text(f"已封禁用户 {user_id}")
    except ValueError:
        update.message.reply_text("效的用户ID")

@handle_error
def unban_user(update, context):
    """解封用户"""
    if not user_manager.is_admin(update.effective_user.id):
        update.message.reply_text("此命令仅管理员可用！")
        return

    if not context.args:
        update.message.reply_text("请提供要解封的用户ID")
        return

    try:
        user_id = int(context.args[0])
        user_manager.unban_user(user_id)
        update.message.reply_text(f"已解封用户 {user_id}")
    except ValueError:
        update.message.reply_text("无效的用户ID")

@handle_error
def set_password(update, context):
    """设置聊天室密码"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    if not room.is_creator(update.effective_user.id):
        update.message.reply_text("只有聊天室创建者才能设置密码！")
        return
        
    if not context.args:
        room.set_password(None)
        update.message.reply_text("已清除聊天室密码")
    else:
        password = context.args[0]
        room.set_password(password)
        update.message.reply_text("已设置聊天室密码")

@handle_error
def room_info(update, context):
    """显示聊天室信息"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    info = f"""
聊天室信息：
ID: {room.room_id}
创建时间: {room.created_at.strftime('%Y-%m-%d %H:%M:%S')}
用户数量: {len(room.users)}/{room.max_users}
是否需要密码: {'是' if room.password else '否'}
过期时间: {room.expire_time.strftime('%Y-%m-%d %H:%M:%S')}
    """
    update.message.reply_text(info)

@handle_error
def mute_user(update, context):
    """禁言用户"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    if not (room.is_creator(update.effective_user.id) or 
            update.effective_user.id in room.admins):
        update.message.reply_text("只有聊天室创建者和管理员才能禁言用户！")
        return
        
    if not context.args:
        update.message.reply_text("请提供要禁言的用户ID")
        return
        
    try:
        user_id = int(context.args[0])
        room.ban_user(user_id)
        update.message.reply_text(f"已禁言用户 {user_id}")
    except ValueError:
        update.message.reply_text("无效的用户ID")

@handle_error
def unmute_user(update, context):
    """解除用户禁言"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    if not (room.is_creator(update.effective_user.id) or 
            update.effective_user.id in room.admins):
        update.message.reply_text("只有聊天室创建者和管理员才能解除禁言！")
        return
        
    if not context.args:
        update.message.reply_text("请提供要解除禁言的用户ID")
        return
        
    try:
        user_id = int(context.args[0])
        room.unban_user(user_id)
        update.message.reply_text(f"已解除用户 {user_id} 的禁言")
    except ValueError:
        update.message.reply_text("无效的用户ID")

@handle_error
def set_announcement(update, context):
    """设置聊天室公告"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    if not room.is_admin(update.effective_user.id):
        update.message.reply_text("只有管理员才能设置公告！")
        return
        
    announcement = ' '.join(context.args) if context.args else None
    room.set_announcement(announcement)
    
    if announcement:
        # 通知所有成员
        for user_id in room.users:
            try:
                context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 新公告：\n\n{announcement}",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Failed to send announcement to user {user_id}: {e}")
        update.message.reply_text("公告已设置并通知所有成员")
    else:
        update.message.reply_text("公告已清除")

@handle_error
def revoke_message(update, context):
    """撤回消息"""
    if not update.message.reply_to_message:
        update.message.reply_text("请回复要撤回的消息")
        return
        
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    # 只允许撤回自己的消息或管理员撤回任何消息
    original_message = update.message.reply_to_message
    if (original_message.from_user.id != update.effective_user.id and 
            not room.is_admin(update.effective_user.id)):
        update.message.reply_text("您只能撤回自己的消息！")
        return
    
    try:
        # 删除原消息
        original_message.delete()
        # 删除撤回命令消息
        update.message.delete()
    except Exception as e:
        logger.error(f"Failed to revoke message: {e}")
        update.message.reply_text("消息撤回失败")

@handle_error
def room_stats(update, context):
    """显示聊天室统计信息"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    stats = room.get_room_stats()
    
    stats_text = f"""
📊 聊天室统计：

基本信息：
• 总消息数：{stats['total_messages']}
• 当前成员：{stats['user_count']}/{room.max_users}
• 已运行时间：{stats['running_time']}

消息类型统计：
• 文字消息：{stats['text_messages']}
• 图片：{stats['photo_messages']}
• 视频：{stats['video_messages']}
• 文件：{stats['document_messages']}
• 语音：{stats['voice_messages']}
• 贴纸：{stats['sticker_messages']}
• GIF：{stats['animation_messages']}

🕒 聊天将在 {stats['expire_in']} 后过期
    """
    update.message.reply_text(stats_text)

@handle_error
def forward_message(update, context):
    """转发消息到其他聊天室"""
    if not update.message.reply_to_message:
        update.message.reply_text("请回复要转发的消息")
        return
        
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    if not context.args:
        update.message.reply_text("请提供目标聊天室ID")
        return
        
    target_room_id = context.args[0]
    if target_room_id not in chat_rooms:
        update.message.reply_text("目标聊天室不存在")
        return
        
    target_room = chat_rooms[target_room_id]
    if not target_room.can_join(update.effective_user.id):
        update.message.reply_text("您无权转发消息到该聊天室")
        return
    
    try:
        original_message = update.message.reply_to_message
        for user_id in target_room.users:
            context.bot.forward_message(
                chat_id=user_id,
                from_chat_id=update.effective_chat.id,
                message_id=original_message.message_id
            )
        update.message.reply_text("消息已转发")
    except Exception as e:
        logger.error(f"Failed to forward message: {e}")
        update.message.reply_text("消息转发失败")

@handle_error
def search_messages(update, context):
    """搜索聊天记录"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    if not context.args:
        update.message.reply_text("请提供搜索关键词")
        return
        
    keyword = ' '.join(context.args).lower()
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    results = room.search_messages(keyword)
    if not results:
        update.message.reply_text("未找到匹配的消息")
        return
        
    response = "搜索结果：\n\n"
    for msg in results[:10]:  # 最多显示10条结果
        user_name = room.get_user_name(msg['user_id'])
        time = msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        content = msg['content']
        if isinstance(content, dict):
            content = content.get('caption', '[媒体文件]')
        response += f"{time} {user_name}: {content}\n\n"
    
    update.message.reply_text(response)

@handle_error
def export_chat(update, context):
    """导出聊天记录"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    if not room.is_admin(update.effective_user.id):
        update.message.reply_text("只有管理员才能导出聊天记录！")
        return
    
    try:
        # 准备导出数据
        export_data = {
            'room_id': room.room_id,
            'created_at': room.created_at.isoformat(),
            'messages': []
        }
        
        for msg in room.messages:
            msg_data = {
                'user_id': msg['user_id'],
                'user_name': room.get_user_name(msg['user_id']),
                'type': msg['type'],
                'timestamp': msg['timestamp'].isoformat()
            }
            
            content = msg['content']
            if isinstance(content, dict):
                msg_data['content'] = content.get('caption', '')
                msg_data['media_type'] = msg['type']
            else:
                msg_data['content'] = content
                
            export_data['messages'].append(msg_data)
        
        # 创建JSON文件
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        file_obj = BytesIO(json_str.encode('utf-8'))
        file_obj.name = f"chat_export_{room_id}.json"
        
        # 发送文件
        update.message.reply_document(
            document=file_obj,
            filename=file_obj.name,
            caption="聊天记录导出文件"
        )
    except Exception as e:
        logger.error(f"Failed to export chat: {e}")
        update.message.reply_text("导出失败，请稍后重试")

@handle_error
def create_poll(update, context):
    """创建投票"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    if not context.args or len(context.args) < 3:
        update.message.reply_text(
            "请按正确格式创建投票：\n"
            "/poll 问题 选项1 选项2 [选项3...]"
        )
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    question = context.args[0]
    options = context.args[1:]
    
    if len(options) > 10:
        update.message.reply_text("选项不能超过10个")
        return
        
    try:
        # 创建投票
        poll_message = context.bot.send_poll(
            chat_id=update.effective_chat.id,
            question=question,
            options=options,
            is_anonymous=False
        )
        
        # 保存投票信息到聊天室
        room.add_poll(poll_message.poll.id, {
            'message_id': poll_message.message_id,
            'question': question,
            'options': options,
            'creator_id': update.effective_user.id,
            'votes': {}
        })
        
        # 转发投票给其他成员
        for user_id in room.users:
            if user_id != update.effective_user.id:
                context.bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=update.effective_chat.id,
                    message_id=poll_message.message_id
                )
                
    except Exception as e:
        logger.error(f"Failed to create poll: {e}")
        update.message.reply_text("创建投票失败，请重试")

@handle_error
def schedule_message(update, context):
    """设置定时消息"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    if len(context.args) < 2:
        update.message.reply_text(
            "请按正确格式设置定时消息：\n"
            "/schedule <分钟> <消息内容>"
        )
        return
        
    try:
        minutes = int(context.args[0])
        if minutes < 1 or minutes > 1440:  # 最多24小时
            update.message.reply_text("定时时间必须在1-1440分钟之间")
            return
            
        message = ' '.join(context.args[1:])
        room_id = context.user_data['current_room']
        room = chat_rooms[room_id]
        
        # 添加定时任务
        job = context.job_queue.run_once(
            send_scheduled_message,
            timedelta(minutes=minutes),
            context={
                'room_id': room_id,
                'message': message,
                'sender_id': update.effective_user.id
            }
        )
        
        # 保存任务信息
        if not hasattr(room, 'scheduled_messages'):
            room.scheduled_messages = []
        room.scheduled_messages.append({
            'job_id': job.job.id,
            'message': message,
            'sender_id': update.effective_user.id,
            'scheduled_time': datetime.now() + timedelta(minutes=minutes)
        })
        
        update.message.reply_text(
            f"定时消息已设置，将在 {minutes} 分钟后发送"
        )
        
    except ValueError:
        update.message.reply_text("无效的时间格式")
    except Exception as e:
        logger.error(f"Failed to schedule message: {e}")
        update.message.reply_text("设置定时消息失败，请重试")

def send_scheduled_message(context):
    """发送定时消息"""
    job = context.job
    data = job.context
    
    room_id = data['room_id']
    if room_id not in chat_rooms:
        return
        
    room = chat_rooms[room_id]
    message = data['message']
    sender_id = data['sender_id']
    
    try:
        for user_id in room.users:
            context.bot.send_message(
                chat_id=user_id,
                text=f"📅 定时消息 来自 {room.get_user_name(sender_id)}：\n\n{message}"
            )
    except Exception as e:
        logger.error(f"Failed to send scheduled message: {e}")

@handle_error
def online_users(update, context):
    """显示在线用户列表"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    online_users = room.get_online_users_list()
    response = "👥 在线用户列表：\n\n"
    
    for user_id in online_users:
        user_name = room.get_user_name(user_id)
        is_admin = "👑" if room.is_admin(user_id) else ""
        is_creator = "⭐️" if room.is_creator(user_id) else ""
        response += f"{user_name} {is_admin}{is_creator}\n"
        
    response += f"\n总计: {len(online_users)}/{len(room.users)} 人在线"
    update.message.reply_text(response)

@handle_error
def read_status(update, context):
    """查看息已读状态"""
    if not update.message.reply_to_message:
        update.message.reply_text("请回复要查看已读状态的消息")
        return
        
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    message_id = update.message.reply_to_message.message_id
    
    read_count = room.get_message_read_count(message_id)
    total_users = len(room.users)
    
    update.message.reply_text(
        f"消息已读状态：{read_count}/{total_users}\n"
        f"已读比例：{read_count/total_users*100:.1f}%"
    )

@handle_error
def set_language(update, context):
    """设置用户语言"""
    if not context.args:
        # 显示可用语言列表
        langs = "\n".join([f"• {code} - {lang['name']}" for code, lang in LANGUAGES.items()])
        update.message.reply_text(
            f"请选择语言 (使用 /setlang <语言代码>)：\n\n{langs}"
        )
        return
        
    lang_code = context.args[0].lower()
    if lang_code not in LANGUAGES:
        update.message.reply_text("不支持的语言！")
        return
        
    user_manager.set_language(update.effective_user.id, lang_code)
    update.message.reply_text(
        get_text('language_set', lang_code)
    )

@handle_error
def set_welcome(update, context):
    """设置自定义欢迎消息"""
    if not context.args:
        update.message.reply_text("请提供欢迎消息内容")
        return
        
    message = ' '.join(context.args)
    user_manager.set_welcome_message(update.effective_user.id, message)
    update.message.reply_text("已设置自定义欢迎消息")

# 修改现有的消息发送函数，使用多语言支持
def send_message(update, context, key, **kwargs):
    """发送多语言消息"""
    lang = user_manager.get_language(update.effective_user.id)
    text = get_text(key, lang, **kwargs)
    update.message.reply_text(text)

@handle_error
def pin_message(update, context):
    """置顶消息"""
    if not update.message.reply_to_message:
        update.message.reply_text("请回复要置顶的消息")
        return
        
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    message_id = update.message.reply_to_message.message_id
    
    if room.pin_message(message_id, update.effective_user.id):
        # 通知所有成员
        for user_id in room.users:
            try:
                context.bot.send_message(
                    chat_id=user_id,
                    text=f"📌 新的置顶消息\n由 {update.effective_user.first_name} 置顶"
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
        update.message.reply_text("消息已置顶")
    else:
        update.message.reply_text("置顶失败（权限不足或已达到置顶上限）")

@handle_error
def unpin_message(update, context):
    """取消置顶消息"""
    if not update.message.reply_to_message:
        update.message.reply_text("请回复要取消置顶的消息")
        return
        
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    message_id = update.message.reply_to_message.message_id
    
    if room.unpin_message(message_id, update.effective_user.id):
        update.message.reply_text("已取消置顶")
    else:
        update.message.reply_text("取消置顶失败（权限不足或消息未置顶）")

@handle_error
def edit_message(update, context):
    """编辑消息"""
    if not update.message.reply_to_message:
        update.message.reply_text("请回复要编辑的消息")
        return
        
    if not context.args:
        update.message.reply_text("请提供新的消息内容")
        return
        
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    message_id = update.message.reply_to_message.message_id
    new_content = ' '.join(context.args)
    
    if room.edit_message(message_id, update.effective_user.id, new_content):
        # 通知所有成员
        for user_id in room.users:
            try:
                context.bot.send_message(
                    chat_id=user_id,
                    text=f"✏️ 消息已编辑\n新内容：{new_content}"
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
        update.message.reply_text("消息已编辑")
    else:
        update.message.reply_text("编辑失败（权限不足或消息不存在）")

@handle_error
def show_pinned(update, context):
    """显示所有置顶消息"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    pinned = room.get_pinned_messages()
    if not pinned:
        update.message.reply_text("当前没有置顶消息")
        return
        
    response = "📌 置顶消息列表：\n\n"
    for msg in pinned:
        user_name = room.get_user_name(msg['user_id'])
        time = msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        content = msg['content']
        if isinstance(content, dict):
            content = content.get('caption', '[媒体文件]')
        response += f"{time} {user_name}:\n{content}\n\n"
    
    update.message.reply_text(response)

@handle_error
def add_auto_reply(update, context):
    """添加自动回复规则"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    if len(context.args) < 2:
        update.message.reply_text(
            "请按正确格式添加自动回复：\n"
            "/autoreply add <关键词> <回复内容>"
        )
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    keyword = context.args[0]
    response = ' '.join(context.args[1:])
    
    if room.add_auto_reply(keyword, response, update.effective_user.id):
        update.message.reply_text(f"已添加自动回复规则：\n关键词：{keyword}\n回复：{response}")
    else:
        update.message.reply_text("添加失败（权限不足）")

@handle_error
def remove_auto_reply(update, context):
    """删除自动回复规则"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    if not context.args:
        update.message.reply_text("请提供要删除的关键词")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    keyword = context.args[0]
    
    if room.remove_auto_reply(keyword, update.effective_user.id):
        update.message.reply_text(f"已删除关键词 '{keyword}' 的自动回复规则")
    else:
        update.message.reply_text("删除失败（权限不足或规则不存在）")

@handle_error
def list_auto_replies(update, context):
    """列出所有自动回复规则"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任���聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    rules = room.get_auto_replies()
    if not rules:
        update.message.reply_text("当前没有自动回复规则")
        return
        
    response = "🤖 自动回复规则列表：\n\n"
    for keyword, rule in rules.items():
        creator_name = room.get_user_name(rule['creator_id'])
        time = rule['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        response += f"关键词：{keyword}\n回复：{rule['response']}\n"
        response += f"创建者：{creator_name}\n创建时间：{time}\n\n"
    
    update.message.reply_text(response)

@handle_error
def add_template(update, context):
    """添加消息模板"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    if len(context.args) < 2:
        update.message.reply_text(
            "请按正确格式添加模板：\n"
            "/template add <模板名称> <模板内容>"
        )
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    name = context.args[0]
    content = ' '.join(context.args[1:])
    
    if room.add_template(name, content, update.effective_user.id):
        update.message.reply_text(f"已添加模板：\n名称：{name}\n内容：{content}")
    else:
        update.message.reply_text("添加失败（权限不足）")

@handle_error
def use_template(update, context):
    """使用消息模板"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    if not context.args:
        update.message.reply_text("请提供模板名称")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    template_name = context.args[0]
    content = room.get_template(template_name)
    
    if content:
        update.message.reply_text(content)
    else:
        update.message.reply_text("模板不存在")

@handle_error
def list_templates(update, context):
    """列出所有消息模板"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    
    templates = room.get_all_templates()
    if not templates:
        update.message.reply_text("当前没有消息模板")
        return
        
    response = "📝 消息模板列表：\n\n"
    for name, template in templates.items():
        creator_name = room.get_user_name(template['creator_id'])
        time = template['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        response += f"名称：{name}\n内容：{template['content']}\n"
        response += f"创建者：{creator_name}\n创建时间：{time}\n\n"
    
    update.message.reply_text(response)

@handle_error
def activity_stats(update, context):
    """显示聊天室活动统计"""
    if 'current_room' not in context.user_data:
        update.message.reply_text("您当前未在任何聊天室中！")
        return
        
    room_id = context.user_data['current_room']
    room = chat_rooms[room_id]
    stats = room.get_room_activity_stats()
    
    response = f"""
📊 聊天室活动统计

消息统计：
• 文字消息：{stats['message_types']['text']}
• 图片：{stats['message_types']['photo']}
• 视频：{stats['message_types']['video']}
• 文件：{stats['message_types']['document']}
• 语音：{stats['message_types']['voice']}
• 贴纸：{stats['message_types']['sticker']}
• GIF：{stats['message_types']['animation']}

用户统计：
• 在线用户：{stats['active_users']}/{stats['total_users']}
• 总消息数：{stats['total_messages']}

时间信息：
• 运行时间：{stats['running_time']}
• 剩余时间：{stats['expire_in']}
"""
    update.message.reply_text(response)

def main():
    """主函数"""
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    dp = updater.dispatcher

    # 创建消息处理器
    message_handler = MessageHandler(chat_rooms)

    # 添加命令处理器
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("new_chat", new_chat))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("leave", leave_chat))
    dp.add_handler(CommandHandler("close", close_chat))
    dp.add_handler(CommandHandler("ban", ban_user))
    dp.add_handler(CommandHandler("unban", unban_user))
    dp.add_handler(CommandHandler("setpass", set_password))
    dp.add_handler(CommandHandler("roominfo", room_info))
    dp.add_handler(CommandHandler("mute", mute_user))
    dp.add_handler(CommandHandler("unmute", unmute_user))
    dp.add_handler(CommandHandler("announce", set_announcement))
    dp.add_handler(CommandHandler("revoke", revoke_message))
    dp.add_handler(CommandHandler("stats", room_stats))
    dp.add_handler(CommandHandler("forward", forward_message))
    dp.add_handler(CommandHandler("search", search_messages))
    dp.add_handler(CommandHandler("export", export_chat))
    dp.add_handler(CommandHandler("poll", create_poll))
    dp.add_handler(CommandHandler("schedule", schedule_message))
    dp.add_handler(CommandHandler("online", online_users))
    dp.add_handler(CommandHandler("read", read_status))
    dp.add_handler(CommandHandler("setlang", set_language))
    dp.add_handler(CommandHandler("setwelcome", set_welcome))
    dp.add_handler(CommandHandler("pin", pin_message))
    dp.add_handler(CommandHandler("unpin", unpin_message))
    dp.add_handler(CommandHandler("edit", edit_message))
    dp.add_handler(CommandHandler("pinned", show_pinned))
    dp.add_handler(CommandHandler("autoreply", add_auto_reply))
    dp.add_handler(CommandHandler("delreply", remove_auto_reply))
    dp.add_handler(CommandHandler("listreplies", list_auto_replies))
    dp.add_handler(CommandHandler("template", add_template))
    dp.add_handler(CommandHandler("use", use_template))
    dp.add_handler(CommandHandler("templates", list_templates))
    dp.add_handler(CommandHandler("activity", activity_stats))
    
    # 添加消息处理器
    dp.add_handler(MessageHandler(
        Filters.text & ~Filters.command, 
        message_handler.handle_message
    ))
    dp.add_handler(MessageHandler(
        Filters.photo | Filters.video | Filters.document | 
        Filters.voice | Filters.sticker | Filters.animation,
        message_handler.handle_message
    ))
    
    # 添加定时清理任务
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_expired_rooms, 'interval', minutes=30)  # 每30分钟清理一次
    scheduler.add_job(cleanup_inactive_users, 'interval', minutes=5)
    scheduler.start()
    
    # 添加错误处理
    dp.add_error_handler(error_callback)
    
    # 启动机器人
    updater.start_polling()
    updater.idle()

def error_callback(update, context):
    """错误处理"""
    try:
        raise context.error
    except Exception as e:
        logger.error(f"Exception while handling an update: {e}")
        if update and update.message:
            update.message.reply_text(
                "发生错误，请稍后重试或联系管理员。"
            )

if __name__ == '__main__':
    # 创建二维码存储目录
    if not os.path.exists('qr_codes'):
        os.makedirs('qr_codes')
    main() 