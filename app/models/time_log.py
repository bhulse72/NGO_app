from datetime import datetime


class TimeLog:
    
    DEFAULT_CATEGORIES = [
        "Mental Health Help",
        "Hazardous",
        "Establishing Contact",
        "Career Counseling"
    ]

    def __init__(self, worker_id, hours, categories, description=None, date=None):
        self.worker_id = worker_id                    # SocialWorker ID
        self.hours = hours                            # float, e.g. 1.5
        self.categories = categories                  # list of strings
        self.description = description                # optional notes
        self.date = date or datetime.now()

    def add_category(self, category):
        if category not in self.categories:
            self.categories.append(category)

    def remove_category(self, category):
        if category in self.categories:
            self.categories.remove(category)

    def __repr__(self):
        return f"<TimeLog {self.worker_id} | {self.hours}hrs on {self.date:%Y-%m-%d} | {self.categories}>"
