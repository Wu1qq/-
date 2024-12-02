from datetime import datetime, timedelta
import time

class ChatRoom:
    def __init__(self, room_id, creator_id):
        self.room_id = room_id
        self.creator_id = creator_id
        self.messages = []
        self.users = set()
        self.created_at = datetime.now()
        self.is_active = True
        self.expire_time = datetime.now() + timedelta(hours=24)  # 24小时后自动过期
        self.banned_users = set()  # 聊天室黑名单
        self.admins = {creator_id}  # 聊天室管理员
        self.max_users = MAX_USERS_PER_ROOM
        self.password = None  # 聊天室密码
        self.pinned_messages = []  # 置顶消息列表
        self.edited_messages = {}  # 消息编辑历史
        self.max_pinned = 3  # 最大置顶消息数量
        self.auto_replies = {}  # 自动回复规则
        self.message_templates = {}  # 消息模板
        self.online_users = {}  # 在线用户列表
        self.online_timeout = 1800  # 在线用户超时时间，30分钟
        
    def add_message(self, user_id, message_type, content):
        """添加消息到聊天室"""
        message = {
            'message_id': len(self.messages) + 1,
            'user_id': user_id,
            'type': message_type,
            'content': content,
            'timestamp': datetime.now()
        }
        self.messages.append(message)
        
    def add_user(self, user_id):
        """添加用户到聊天室"""
        self.users.add(user_id)
        
    def remove_user(self, user_id):
        """从聊天室移除用户"""
        self.users.remove(user_id)
        
    def close_room(self):
        """关闭聊天室"""
        self.is_active = False
        self.messages.clear()
        self.users.clear()
        
    def is_expired(self):
        """检查聊天室是否过期"""
        return datetime.now() > self.expire_time 
        
    def is_creator(self, user_id):
        """检查用户是否是聊天室创建者"""
        return user_id == self.creator_id
        
    def set_password(self, password: str):
        """设置聊天室密码"""
        self.password = password
        
    def check_password(self, password: str) -> bool:
        """检查密码是否正确"""
        return not self.password or self.password == password
        
    def add_admin(self, user_id: int):
        """添加管理员"""
        self.admins.add(user_id)
        
    def remove_admin(self, user_id: int):
        """移除管理员"""
        if user_id != self.creator_id:  # 创建者不能被移除管理员权限
            self.admins.discard(user_id)
            
    def ban_user(self, user_id: int):
        """将用户加入黑名单"""
        if user_id != self.creator_id:
            self.banned_users.add(user_id)
            if user_id in self.users:
                self.remove_user(user_id)
                
    def unban_user(self, user_id: int):
        """将用户从黑名单中移除"""
        self.banned_users.discard(user_id)
        
    def can_join(self, user_id: int) -> bool:
        """检查用户是否可以加入聊天室"""
        return (user_id not in self.banned_users and 
                len(self.users) < self.max_users)
        
    def get_user_name(self, user_id: int) -> str:
        """获取用户昵称"""
        # 这里需要实现从 Telegram 获取用户信息的逻辑
        return f"用户 {user_id}"
        
    def get_message_history(self, limit: int = 50) -> list:
        """获取聊天记录"""
        return self.messages[-limit:]
        
    def get_online_users(self) -> set:
        """获取在线用户"""
        return self.users
        
    def get_room_stats(self) -> dict:
        """获取聊天室统计信息"""
        return {
            'total_messages': len(self.messages),
            'user_count': len(self.users),
            'created_time': self.created_at,
            'expire_time': self.expire_time,
            'is_active': self.is_active
        }
        
    def extend_expire_time(self, hours: int = 24):
        """延长聊天室过期时间"""
        self.expire_time = datetime.now() + timedelta(hours=hours)
        
    def set_max_users(self, max_users: int):
        """设置最大用户数"""
        self.max_users = max_users
        
    def is_full(self) -> bool:
        """检查聊天室是否已满"""
        return len(self.users) >= self.max_users
        
    def get_admin_list(self) -> set:
        """获取管理员列表"""
        return self.admins
        
    def is_admin(self, user_id: int) -> bool:
        """检查用户是否是管理员"""
        return user_id in self.admins or user_id == self.creator_id
        
    def set_announcement(self, announcement: str = None):
        """设置聊天室公告"""
        self.announcement = announcement
        self.announcement_time = datetime.now() if announcement else None
        
    def get_announcement(self) -> dict:
        """获取聊天室公告"""
        if not hasattr(self, 'announcement') or not self.announcement:
            return None
        return {
            'text': self.announcement,
            'time': self.announcement_time
        }
        
    def revoke_message(self, message_id: int) -> bool:
        """撤回消息"""
        for i, msg in enumerate(self.messages):
            if msg.get('message_id') == message_id:
                self.messages.pop(i)
                return True
        return False
        
    def pin_message(self, message_id: int, user_id: int) -> bool:
        """置顶消息"""
        if not self.is_admin(user_id):
            return False
            
        if len(self.pinned_messages) >= self.max_pinned:
            return False
            
        for msg in self.messages:
            if msg.get('message_id') == message_id:
                if message_id not in self.pinned_messages:
                    self.pinned_messages.append(message_id)
                return True
        return False
        
    def unpin_message(self, message_id: int, user_id: int) -> bool:
        """取消置顶消息"""
        if not self.is_admin(user_id):
            return False
            
        if message_id in self.pinned_messages:
            self.pinned_messages.remove(message_id)
            return True
        return False
        
    def get_pinned_messages(self) -> list:
        """获取所有置顶消息"""
        pinned = []
        for msg in self.messages:
            if msg.get('message_id') in self.pinned_messages:
                pinned.append(msg)
        return pinned
        
    def edit_message(self, message_id: int, user_id: int, new_content: str) -> bool:
        """编辑消息"""
        for msg in self.messages:
            if msg.get('message_id') == message_id:
                if msg['user_id'] != user_id and not self.is_admin(user_id):
                    return False
                    
                # 保存编辑历史
                if message_id not in self.edited_messages:
                    self.edited_messages[message_id] = []
                self.edited_messages[message_id].append({
                    'old_content': msg['content'],
                    'edit_time': datetime.now(),
                    'editor_id': user_id
                })
                
                msg['content'] = new_content
                msg['edited'] = True
                msg['last_edit_time'] = datetime.now()
                return True
        return False
        
    def get_edit_history(self, message_id: int) -> list:
        """获取消息编辑历史"""
        return self.edited_messages.get(message_id, [])
        
    def add_auto_reply(self, keyword: str, response: str, user_id: int) -> bool:
        """添加自动回复规则"""
        if not self.is_admin(user_id):
            return False
            
        self.auto_replies[keyword.lower()] = {
            'response': response,
            'creator_id': user_id,
            'created_at': datetime.now()
        }
        return True
        
    def remove_auto_reply(self, keyword: str, user_id: int) -> bool:
        """删除自动回复规则"""
        if not self.is_admin(user_id):
            return False
            
        if keyword.lower() in self.auto_replies:
            del self.auto_replies[keyword.lower()]
            return True
        return False
        
    def get_auto_replies(self) -> dict:
        """获取所有自动回复规则"""
        return self.auto_replies
        
    def check_auto_reply(self, message: str) -> str:
        """检查是否触发自动回复"""
        message = message.lower()
        for keyword, rule in self.auto_replies.items():
            if keyword in message:
                return rule['response']
        return None
        
    def add_template(self, name: str, content: str, user_id: int) -> bool:
        """添加消息模板"""
        if not self.is_admin(user_id):
            return False
            
        self.message_templates[name] = {
            'content': content,
            'creator_id': user_id,
            'created_at': datetime.now()
        }
        return True
        
    def remove_template(self, name: str, user_id: int) -> bool:
        """删除消息模板"""
        if not self.is_admin(user_id):
            return False
            
        if name in self.message_templates:
            del self.message_templates[name]
            return True
        return False
        
    def get_template(self, name: str) -> str:
        """获取消息模板"""
        return self.message_templates.get(name, {}).get('content')
        
    def get_all_templates(self) -> dict:
        """获取所有消息模板"""
        return self.message_templates
        
    def get_online_users_list(self) -> list:
        """获取在线用户列表"""
        current_time = time.time()
        return [user_id for user_id, last_active in self.online_users.items()
                if current_time - last_active < self.online_timeout]
        
    def update_user_activity(self, user_id: int):
        """更新用户活动状态"""
        self.online_users[user_id] = time.time()
        
    def get_user_status(self, user_id: int) -> str:
        """获取用户状态"""
        if user_id not in self.users:
            return "未加入"
        if user_id in self.banned_users:
            return "已禁言"
        if self.is_creator(user_id):
            return "创建者"
        if user_id in self.admins:
            return "管理员"
        if user_id in self.get_online_users_list():
            return "在线"
        return "离线"
        
    def get_room_activity_stats(self) -> dict:
        """获取聊天室活动统计"""
        message_types = {
            'text': 0,
            'photo': 0,
            'video': 0,
            'document': 0,
            'voice': 0,
            'sticker': 0,
            'animation': 0
        }
        
        for msg in self.messages:
            msg_type = msg.get('type')
            if msg_type in message_types:
                message_types[msg_type] += 1
                
        return {
            'message_types': message_types,
            'total_messages': len(self.messages),
            'active_users': len(self.get_online_users_list()),
            'total_users': len(self.users),
            'running_time': str(datetime.now() - self.created_at).split('.')[0],
            'expire_in': str(self.expire_time - datetime.now()).split('.')[0]
        }