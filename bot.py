from telegram.ext import (
    Updater, CommandHandler, MessageHandler as TelegramMessageHandler,
    Filters
)
from message_handler import MessageHandler as CustomMessageHandler
from telegram import ParseMode
import logging
import os
import qrcode
from datetime import datetime, timedelta
import uuid
from chat_room import ChatRoom
from apscheduler.schedulers.background import BackgroundScheduler
import glob
import functools
from config import *
from user_manager import UserManager
import json
from io import BytesIO
import time
from languages import get_text, LANGUAGES
from config import BOT_TOKEN, BOT_USERNAME
import pytz
import base64
import ssl
import certifi

# 配置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储聊天室信息
chat_rooms = {}
user_manager = UserManager()

def main():
    """主函数"""
    print(f"Using token: {BOT_TOKEN}")
    logger.info("Starting bot...")
    
    try:
        # 配置代理
        server = "120.241.144.225"
        port = 10575
        secret = "eedb2dcbee75faa6f5bf10dda691437828617a7572652e6d6963726f736f66742e636f6d"
        
        # 解码secret
        secret_bytes = bytes.fromhex(secret)
        domain = "microsoft.com"
        secret_with_domain = secret_bytes + domain.encode()
        encoded_secret = base64.b64encode(secret_with_domain).decode()
        
        # 配置SSL上下文
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        
        # 配置代理
        request_kwargs = {
            'proxy_url': f'https://{server}:{port}',
            'urllib3_proxy_kwargs': {
                'ssl_context': ssl_context,
                'assert_hostname': domain,
                'headers': {
                    'X-MTProto-Secret': encoded_secret,
                    'Host': domain
                }
            },
            'connect_timeout': 60.0,
            'read_timeout': 60.0,
            'bootstrap_retries': 5,
            'connect_retries': 5,
            'read_retries': 5
        }
        
        # 创建updater
        updater = Updater(
            token=BOT_TOKEN,
            use_context=True,
            request_kwargs=request_kwargs,
            workers=4,
            base_url='https://api.telegram.org/bot'
        )
        logger.info("Bot updater created successfully")

        dp = updater.dispatcher
        logger.info("Setting up command handlers...")

        # 创建消息处理器
        message_handler = CustomMessageHandler(chat_rooms)

        # 添加命令处理器
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("new_chat", new_chat))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("leave", leave_chat))
        dp.add_handler(CommandHandler("close", close_chat))
        logger.info("Command handlers registered")

        # 添加消息处理器
        dp.add_handler(TelegramMessageHandler(
            Filters.text & ~Filters.command,
            message_handler.handle_message
        ))
        logger.info("Message handler registered")

        # 添加错误处理器
        dp.add_error_handler(error_callback)
        logger.info("Error handler registered")

        # 启动机器人
        logger.info("Starting polling...")
        updater.start_polling(
            timeout=30,
            read_latency=2.0,
            drop_pending_updates=True
        )
        
        # 启动调度器
        scheduler = BackgroundScheduler()
        scheduler.start()
        logger.info("Bot is running!")
        
        # 保持运行
        updater.idle()
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise