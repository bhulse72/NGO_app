from datetime import datetime, timedelta
from app.models.contact import Contact


class Client(Contact):
    
    RISK_LEVELS = [
        "Not at risk",
        "Low risk",
        "High risk",
        "Needs urgent help",
        "Threat to others",
        "Threat to themselves"
    ]

    def __init__(self, assigned_to, inactivity_days=90, **kwargs):
        super().__init__(**kwargs)

        # Case info
        self.assigned_to = assigned_to          # SocialWorker ID
        self.client_since = datetime.now()
        self.risk_level = "Not at risk"

        # Active/inactive
        self.is_active = True
        self.inactivity_days = inactivity_days  # customizable threshold
        self.last_activity_date = datetime.now()

        # Notes
        self.notes = []                         # list of Note objects, added later

    def set_risk_level(self, level):
        if level not in self.RISK_LEVELS:
            raise ValueError(f"Invalid risk level. Choose from: {self.RISK_LEVELS}")
        self.risk_level = level

    def log_activity(self):
        """Call this whenever a note is added or meaningful action is taken"""
        self.last_activity_date = datetime.now()
        self.is_active = True

    def check_inactivity(self):
        """Automatically sets client to inactive if threshold has passed"""
        cutoff = datetime.now() - timedelta(days=self.inactivity_days)
        if self.last_activity_date < cutoff:
            self.is_active = False

    def add_note(self, note):
        """Add a note and log activity"""
        self.notes.append(note)
        self.log_activity()

    def get_notes(self):
        """Returns notes most recent first"""
        return sorted(self.notes, key=lambda n: n.created_at, reverse=True)

    def __repr__(self):
        return f"<Client {self.contact_id}: {self.name} | {self.risk_level}>"