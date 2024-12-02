from telegram import ParseMode, Update
from telegram.ext import CallbackContext
import os
import magic
from config import *

class MessageHandler:
    def __init__(self, chat_rooms):
        self.chat_rooms = chat_rooms
        
    async def handle_message(self, update: Update, context: CallbackContext):
        """处理接收到的消息"""
        if not update.message:
            return
            
        user_id = update.effective_user.id
        room_id = context.user_data.get('current_room')
        
        if not room_id or room_id not in self.chat_rooms:
            update.message.reply_text("请先加入聊天室！")
            return
            
        room = self.chat_rooms[room_id]
        
        # 更新用户活动状态
        room.update_user_activity(user_id)
        
        # 检查用户是否被禁言
        if user_id in room.banned_users:
            update.message.reply_text("您已被禁止在此聊天室发言")
            return
            
        try:
            # 处理不同类型的消息
            if update.message.text:
                # 检查自动回复
                auto_reply = room.check_auto_reply(update.message.text)
                if auto_reply:
                    await update.message.reply_text(auto_reply)
                # 继续处理文本消息
                await self._handle_text(update, context, room, user_id)
            elif update.message.photo:
                await self._handle_photo(update, context, room, user_id)
            elif update.message.video:
                await self._handle_video(update, context, room, user_id)
            elif update.message.document:
                await self._handle_document(update, context, room, user_id)
            elif update.message.voice:
                await self._handle_voice(update, context, room, user_id)
            elif update.message.sticker:
                await self._handle_sticker(update, context, room, user_id)
            elif update.message.animation:
                await self._handle_animation(update, context, room, user_id)
        except Exception as e:
            update.message.reply_text("消息发送失败，请重试")
            raise e

    async def _handle_text(self, update, context, room, user_id):
        """处理文本消息"""
        text = update.message.text
        if len(text) > MAX_MESSAGE_LENGTH:
            update.message.reply_text(f"消息长度不能超过 {MAX_MESSAGE_LENGTH} 字符")
            return
            
        room.add_message(user_id, 'text', text)
        await self._broadcast_text(context, room, user_id, text)

    async def _handle_photo(self, update, context, room, user_id):
        """处理图片消息"""
        photo = update.message.photo[-1]  # 获取最大尺寸的图片
        if photo.file_size > MAX_FILE_SIZE:
            update.message.reply_text("图片大小超过限制")
            return
            
        file = await photo.get_file()
        file_path = f"{MEDIA_DIR}/{room.room_id}_{file.file_id}.jpg"
        await file.download_to_drive(file_path)
        
        caption = update.message.caption or ""
        room.add_message(user_id, 'photo', {'path': file_path, 'caption': caption})
        await self._broadcast_photo(context, room, user_id, file_path, caption)

    async def _handle_video(self, update, context, room, user_id):
        """处理视频消息"""
        video = update.message.video
        if video.file_size > MAX_FILE_SIZE:
            update.message.reply_text("视频大小超过限制")
            return
            
        file = await video.get_file()
        file_path = f"{MEDIA_DIR}/{room.room_id}_{file.file_id}.mp4"
        await file.download_to_drive(file_path)
        
        caption = update.message.caption or ""
        room.add_message(user_id, 'video', {'path': file_path, 'caption': caption})
        await self._broadcast_video(context, room, user_id, file_path, caption)

    async def _handle_document(self, update, context, room, user_id):
        """处理文件消息"""
        doc = update.message.document
        if doc.file_size > MAX_FILE_SIZE:
            update.message.reply_text("文件大小超过限制")
            return
            
        file = await doc.get_file()
        file_path = f"{MEDIA_DIR}/{room.room_id}_{file.file_id}_{doc.file_name}"
        await file.download_to_drive(file_path)
        
        # 检查文件类型是否允许
        if not self._check_file_type(file_path, ALLOWED_FILE_TYPES['document']):
            os.remove(file_path)
            update.message.reply_text("不支持的文件类型")
            return
            
        caption = update.message.caption or ""
        room.add_message(user_id, 'document', {
            'path': file_path, 
            'caption': caption,
            'file_name': doc.file_name
        })
        await self._broadcast_document(context, room, user_id, file_path, doc.file_name, caption)

    async def _handle_voice(self, update, context, room, user_id):
        """处理语音消息"""
        voice = update.message.voice
        if voice.file_size > MAX_FILE_SIZE:
            update.message.reply_text("语音消息大小超过限制")
            return
            
        file = await voice.get_file()
        file_path = f"{MEDIA_DIR}/{room.room_id}_{file.file_id}.ogg"
        await file.download_to_drive(file_path)
        
        caption = update.message.caption or ""
        room.add_message(user_id, 'voice', {'path': file_path, 'caption': caption})
        await self._broadcast_voice(context, room, user_id, file_path, caption)

    async def _handle_sticker(self, update, context, room, user_id):
        """处理贴纸消息"""
        sticker = update.message.sticker
        file = await sticker.get_file()
        file_path = f"{MEDIA_DIR}/{room.room_id}_{file.file_id}.webp"
        await file.download_to_drive(file_path)
        
        room.add_message(user_id, 'sticker', {'path': file_path})
        await self._broadcast_sticker(context, room, user_id, file_path)

    async def _handle_animation(self, update, context, room, user_id):
        """处理GIF动图消息"""
        animation = update.message.animation
        if animation.file_size > MAX_FILE_SIZE:
            update.message.reply_text("GIF大小超过限制")
            return
            
        file = await animation.get_file()
        file_path = f"{MEDIA_DIR}/{room.room_id}_{file.file_id}.gif"
        await file.download_to_drive(file_path)
        
        caption = update.message.caption or ""
        room.add_message(user_id, 'animation', {'path': file_path, 'caption': caption})
        await self._broadcast_animation(context, room, user_id, file_path, caption)

    async def _broadcast_text(self, context, room, sender_id, text):
        """广播文本消息"""
        sender = await context.bot.get_chat_member(sender_id, sender_id)
        sender_name = sender.user.first_name
        
        for user_id in room.users:
            if user_id != sender_id:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"{sender_name}: {text}",
                    parse_mode=ParseMode.HTML
                )

    async def _broadcast_photo(self, context, room, sender_id, file_path, caption):
        """广播图片消息"""
        sender = await context.bot.get_chat_member(sender_id, sender_id)
        sender_name = sender.user.first_name
        
        for user_id in room.users:
            if user_id != sender_id:
                with open(file_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption=f"{sender_name}: {caption}" if caption else sender_name,
                        parse_mode=ParseMode.HTML
                    )

    async def _broadcast_video(self, context, room, sender_id, file_path, caption):
        """广播视频消息"""
        sender = await context.bot.get_chat_member(sender_id, sender_id)
        sender_name = sender.user.first_name
        
        for user_id in room.users:
            if user_id != sender_id:
                with open(file_path, 'rb') as video:
                    await context.bot.send_video(
                        chat_id=user_id,
                        video=video,
                        caption=f"{sender_name}: {caption}" if caption else sender_name,
                        parse_mode=ParseMode.HTML
                    )

    async def _broadcast_document(self, context, room, sender_id, file_path, file_name, caption):
        """广播文件消息"""
        sender = await context.bot.get_chat_member(sender_id, sender_id)
        sender_name = sender.user.first_name
        
        for user_id in room.users:
            if user_id != sender_id:
                with open(file_path, 'rb') as doc:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=doc,
                        filename=file_name,
                        caption=f"{sender_name}: {caption}" if caption else sender_name,
                        parse_mode=ParseMode.HTML
                    )

    async def _broadcast_voice(self, context, room, sender_id, file_path, caption):
        """广播语音消息"""
        sender = await context.bot.get_chat_member(sender_id, sender_id)
        sender_name = sender.user.first_name
        
        for user_id in room.users:
            if user_id != sender_id:
                with open(file_path, 'rb') as voice:
                    await context.bot.send_voice(
                        chat_id=user_id,
                        voice=voice,
                        caption=f"{sender_name}: {caption}" if caption else sender_name,
                        parse_mode=ParseMode.HTML
                    )

    async def _broadcast_sticker(self, context, room, sender_id, file_path):
        """广播贴纸消息"""
        sender = await context.bot.get_chat_member(sender_id, sender_id)
        sender_name = sender.user.first_name
        
        for user_id in room.users:
            if user_id != sender_id:
                with open(file_path, 'rb') as sticker:
                    await context.bot.send_sticker(
                        chat_id=user_id,
                        sticker=sticker
                    )

    async def _broadcast_animation(self, context, room, sender_id, file_path, caption):
        """广播GIF动图消息"""
        sender = await context.bot.get_chat_member(sender_id, sender_id)
        sender_name = sender.user.first_name
        
        for user_id in room.users:
            if user_id != sender_id:
                with open(file_path, 'rb') as animation:
                    await context.bot.send_animation(
                        chat_id=user_id,
                        animation=animation,
                        caption=f"{sender_name}: {caption}" if caption else sender_name,
                        parse_mode=ParseMode.HTML
                    )

    def _check_file_type(self, file_path, allowed_types):
        """检查文件类型是否允许"""
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        return file_type in allowed_types

    async def _get_file_info(self, file_path):
        """获取文件信息"""
        try:
            file_size = os.path.getsize(file_path)
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(file_path)
            return {
                'size': file_size,
                'type': file_type
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None

try:
    import magic
except ImportError:
    import sys
    if sys.platform == 'win32':
        print("请安装 python-magic-bin")
        # pip install python-magic-bin
    else:
        print("请安装 python-magic 和系统依赖")
        # sudo apt-get install libmagic1
        # pip install python-magic
    raise