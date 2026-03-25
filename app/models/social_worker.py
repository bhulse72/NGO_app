from datetime import datetime


class SocialWorker:
    def __init__(self, worker_id, name, email, is_admin=False):
        self.worker_id = worker_id
        self.name = name
        self.email = email                  # gmail, will be used for auth later
        self.is_admin = is_admin            # True if they also have admin role

        self.assigned_clients = []          # list of client IDs
        self.time_logs = []                 # list of TimeLog objects

    def assign_client(self, client_id):
        if client_id not in self.assigned_clients:
            self.assigned_clients.append(client_id)

    def unassign_client(self, client_id):
        if client_id in self.assigned_clients:
            self.assigned_clients.remove(client_id)

    def log_time(self, time_log):
        self.time_logs.append(time_log)

    def get_hours_by_category(self):
        """Returns a dict of category -> total hours"""
        totals = {}
        for log in self.time_logs:
            for category in log.categories:
                totals[category] = totals.get(category, 0) + log.hours
        return totals

    def __repr__(self):
        role = "Admin/Social Worker" if self.is_admin else "Social Worker"
        return f"<{role} {self.worker_id}: {self.name}>"