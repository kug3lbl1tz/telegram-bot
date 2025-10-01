# print_request.py
import uuid

class PrintRequest:
    def __init__(self, username, user_id, file_id, caption, id=None, status="pending"):
        self.id = id or str(uuid.uuid4())[:8]
        self.username = username
        self.user_id = user_id
        self.file_id = file_id
        self.caption = caption
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "user_id": self.user_id,
            "file_id": self.file_id,
            "caption": self.caption,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict):
        # tolerate missing fields and provide defaults
        return cls(
            username=data.get("username"),
            user_id=data.get("user_id"),
            file_id=data.get("file_id"),
            caption=data.get("caption"),
            id=data.get("id"),
            status=data.get("status", "pending"),
        )