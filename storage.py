import json
from datetime import datetime, timedelta

class DialogueStorage:
    def __init__(self, filename='dialogues.json'):
        self.filename = filename
        self.dialogues = self.load_dialogues()

    def load_dialogues(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_dialogues(self):
        with open(self.filename, 'w') as f:
            json.dump(self.dialogues, f)

    def add_message(self, chat_id, role, content):
        if chat_id not in self.dialogues:
            self.dialogues[chat_id] = []
        self.dialogues[chat_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save_dialogues()

    def get_messages(self, chat_id, max_messages=7):
        if chat_id in self.dialogues:
            return self.dialogues[chat_id][-max_messages:]
        return []

    def clean_old_messages(self, max_age_hours=24):
        current_time = datetime.now()
        for chat_id in self.dialogues:
            self.dialogues[chat_id] = [
                msg for msg in self.dialogues[chat_id]
                if (current_time - datetime.fromisoformat(msg['timestamp'])) < timedelta(hours=max_age_hours)
            ]
        self.save_dialogues()

dialogue_storage = DialogueStorage()