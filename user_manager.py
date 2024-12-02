from datetime import datetime
from typing import Dict, Set
from languages import DEFAULT_LANGUAGE

class UserManager:
    def __init__(self):
        self.user_rooms: Dict[int, Set[str]] = {}  # 用户ID -> 房间ID集合
        self.banned_users: Set[int] = set()  # 被封禁的用户ID
        self.admin_users: Set[int] = {12345}  # 管理员用户ID，初始添加一个管理员
        self.user_settings = {}  # 用户设置

    def add_room_to_user(self, user_id: int, room_id: str) -> bool:
        """为用户添加聊天室"""
        if user_id in self.banned_users:
            return False
        
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
            
        self.user_rooms[user_id].add(room_id)
        return True

    def remove_room_from_user(self, user_id: int, room_id: str):
        """从用户移除聊天室"""
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)

    def can_create_room(self, user_id: int) -> bool:
        """检查用户是否可以创建新的聊天室"""
        if user_id in self.banned_users:
            return False
        return len(self.user_rooms.get(user_id, set())) < MAX_ROOMS_PER_USER

    def ban_user(self, user_id: int):
        """封禁用户"""
        self.banned_users.add(user_id)

    def unban_user(self, user_id: int):
        """解封用户"""
        self.banned_users.discard(user_id)

    def is_admin(self, user_id: int) -> bool:
        """检查用户是否是管理员"""
        return user_id in self.admin_users

    def add_admin(self, user_id: int):
        """添加管理员"""
        self.admin_users.add(user_id)

    def set_language(self, user_id: int, language: str):
        """设置用户语言"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        self.user_settings[user_id]['language'] = language
        
    def get_language(self, user_id: int) -> str:
        """获取用户语言设置"""
        return self.user_settings.get(user_id, {}).get('language', DEFAULT_LANGUAGE)
        
    def set_welcome_message(self, user_id: int, message: str):
        """设置自定义欢迎消息"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        self.user_settings[user_id]['welcome_message'] = message
        
    def get_welcome_message(self, user_id: int) -> str:
        """获取用户自定义欢迎消息"""
        return self.user_settings.get(user_id, {}).get('welcome_message')
  