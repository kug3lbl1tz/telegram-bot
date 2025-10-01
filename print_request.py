import uuid

class PrintRequest:
    def __init__(self, username, userid, file_id, caption):
        self.id = str(uuid.uuid4())[:8]
        self.username = username
        self.userid = userid
        self.file_id = file_id
        self.caption = caption
        self.status = "pending"