from datetime import datetime


class Note:
    def __init__(self, author, text, attachments=None):
        self.author = author                          # SocialWorker ID
        self.text = text
        self.attachments: list[str] = attachments or []  # file paths or URLs
        self.created_at = datetime.now()

    def add_attachment(self, file_path):
        self.attachments.append(file_path)

    def __repr__(self):
        return f"<Note by {self.author} at {self.created_at:%Y-%m-%d %H:%M}>"