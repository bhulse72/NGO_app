import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from config import SPREADSHEET_ID, CREDENTIALS_FILE

from app.models.contact import Contact, RelatedPerson, ContactAttempt
from app.models.client import Client
from app.models.note import Note
from app.models.social_worker import SocialWorker
from app.models.time_log import TimeLog
import time

_cache = {}
CACHE_TTL = 60  # seconds

def get_cached(key, loader_fn):
    now = time.time()
    if key not in _cache or now - _cache[key]["time"] > CACHE_TTL:
        _cache[key] = {"data": loader_fn(), "time": now}
    return _cache[key]["data"]


# Google Sheets scope
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet(tab_name):
    """Returns a gspread worksheet by tab name"""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet(tab_name)


# ── Contacts ──────────────────────────────────────────────

def save_contact(contact: Contact):
    sheet = get_sheet("Contacts")
    sheet.append_row([
        contact.contact_id,
        contact.name,
        contact.date_of_birth.strftime("%Y-%m-%d") if contact.date_of_birth else "",
        contact.phone,
        contact.address,
        contact.referral_source,
        contact.referral_date.strftime("%Y-%m-%d") if contact.referral_date else "",
        contact.referral_description,
        contact.photo or "",
        contact.added_by,
        contact.date_added.strftime("%Y-%m-%d %H:%M:%S")
    ])
    # Save related people and contact attempts too
    for person in contact.related_people:
        save_related_person(contact.contact_id, person)
    for attempt in contact.contact_attempts:
        save_contact_attempt(contact.contact_id, attempt)


def load_all_contacts():
    return get_cached("contacts", _load_all_contacts_from_sheet)

def _load_all_contacts_from_sheet():
    sheet = get_sheet("Contacts")
    rows = sheet.get_all_records()
    
    # Load all contact attempts grouped by contact_id
    attempts_sheet = get_sheet("Contact_Attempts")
    attempt_rows = attempts_sheet.get_all_records()
    attempts_by_id = {}
    for row in attempt_rows:
        cid = row["contact_id"]
        if cid not in attempts_by_id:
            attempts_by_id[cid] = []
        from app.models.contact import ContactAttempt
        attempt = ContactAttempt(
            date=datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S"),
            reached=row["reached"] == "True",
            reached_via=row["reached_via"],
            notes=row["notes"] or None
        )
        attempts_by_id[cid].append(attempt)

    contacts = []
    for row in rows:
        contact = Contact(
            contact_id=row["contact_id"],
            name=row["name"],
            date_of_birth=datetime.strptime(row["date_of_birth"], "%Y-%m-%d") if row["date_of_birth"] else None,
            phone=row["phone"],
            address=row["address"],
            referral_source=row["referral_source"],
            referral_date=datetime.strptime(row["referral_date"], "%Y-%m-%d") if row["referral_date"] else None,
            referral_description=row["referral_description"],
            added_by=row["added_by"],
            photo=row["photo"] or None
        )
        contact.contact_attempts = attempts_by_id.get(contact.contact_id, [])
        contacts.append(contact)
    return contacts

# ── Related People ────────────────────────────────────────

def save_related_person(contact_id, person: RelatedPerson):
    sheet = get_sheet("Related_People")
    sheet.append_row([
        contact_id,
        person.name,
        person.relationship,
        person.phone or "",
        person.address or ""
    ])


# ── Contact Attempts ──────────────────────────────────────

def save_contact_attempt(contact_id, attempt: ContactAttempt):
    sheet = get_sheet("Contact_Attempts")
    sheet.append_row([
        contact_id,
        attempt.date.strftime("%Y-%m-%d %H:%M:%S"),
        str(attempt.reached),
        attempt.reached_via,
        attempt.notes or ""
    ])


# ── Clients ───────────────────────────────────────────────

def save_client(client: Client):
    save_contact(client)  # save base contact fields first
    sheet = get_sheet("Clients")
    sheet.append_row([
        client.contact_id,
        client.assigned_to,
        client.client_since.strftime("%Y-%m-%d %H:%M:%S"),
        client.risk_level,
        str(client.is_active),
        client.inactivity_days,
        client.last_activity_date.strftime("%Y-%m-%d %H:%M:%S")
    ])
    for note in client.notes:
        save_note(client.contact_id, note)


def load_all_clients():
    client_sheet = get_sheet("Clients")
    client_rows = {row["contact_id"]: row for row in client_sheet.get_all_records()}

    # Load notes grouped by contact_id
    notes_sheet = get_sheet("Notes")
    note_rows = notes_sheet.get_all_records()
    notes_by_id = {}
    for row in note_rows:
        cid = row["contact_id"]
        if cid not in notes_by_id:
            notes_by_id[cid] = []
        note = Note(
            author=row["author"],
            text=row["text"],
            attachments=row["attachments"].split(",") if row["attachments"] else []
        )
        note.created_at = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
        notes_by_id[cid].append(note)

    # Load related people grouped by contact_id
    related_sheet = get_sheet("Related_People")
    related_rows = related_sheet.get_all_records()
    related_by_id = {}
    for row in related_rows:
        cid = row["contact_id"]
        if cid not in related_by_id:
            related_by_id[cid] = []
        related_by_id[cid].append(RelatedPerson(
            name=row["name"],
            relationship=row["relationship"],
            phone=row["phone"] or None,
            address=row["address"] or None
        ))

    contacts = load_all_contacts()
    clients = []
    for contact in contacts:
        if contact.contact_id in client_rows:
            row = client_rows[contact.contact_id]
            client = Client(
                contact_id=contact.contact_id,
                name=contact.name,
                date_of_birth=contact.date_of_birth,
                phone=contact.phone,
                address=contact.address,
                referral_source=contact.referral_source,
                referral_date=contact.referral_date,
                referral_description=contact.referral_description,
                added_by=contact.added_by,
                photo=contact.photo,
                assigned_to=row["assigned_to"],
                inactivity_days=int(row["inactivity_days"])
            )
            client.risk_level = row["risk_level"]
            client.is_active = row["is_active"] == "True"
            client.client_since = datetime.strptime(row["client_since"], "%Y-%m-%d %H:%M:%S")
            client.last_activity_date = datetime.strptime(row["last_activity_date"], "%Y-%m-%d %H:%M:%S")
            client.related_people = related_by_id.get(contact.contact_id, [])
            client.contact_attempts = contact.contact_attempts
            client.notes = notes_by_id.get(contact.contact_id, [])
            clients.append(client)
    return clients


# ── Notes ─────────────────────────────────────────────────

def save_note(contact_id, note: Note):
    sheet = get_sheet("Notes")
    sheet.append_row([
        contact_id,
        note.author,
        note.text,
        ",".join(note.attachments),
        note.created_at.strftime("%Y-%m-%d %H:%M:%S")
    ])


# ── Social Workers ────────────────────────────────────────

def save_social_worker(worker: SocialWorker):
    sheet = get_sheet("Social_Workers")
    sheet.append_row([
        worker.worker_id,
        worker.name,
        worker.email,
        str(worker.is_admin),
        ",".join(worker.assigned_clients)
    ])


def load_all_social_workers():
    sheet = get_sheet("Social_Workers")
    rows = sheet.get_all_records()

    # Load time logs grouped by worker_id
    logs_sheet = get_sheet("Time_Logs")
    log_rows = logs_sheet.get_all_records()
    logs_by_id = {}
    for row in log_rows:
        wid = row["worker_id"]
        if wid not in logs_by_id:
            logs_by_id[wid] = []
        log = TimeLog(
            worker_id=row["worker_id"],
            hours=float(row["hours"]),
            categories=row["categories"].split(",") if row["categories"] else [],
            description=row["description"] or None,
            date=datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S")
        )
        logs_by_id[wid].append(log)

    workers = []
    for row in rows:
        worker = SocialWorker(
            worker_id=row["worker_id"],
            name=row["name"],
            email=row["email"],
            is_admin=row["is_admin"] == "True"
        )
        worker.assigned_clients = row["assigned_clients"].split(",") if row["assigned_clients"] else []
        worker.time_logs = logs_by_id.get(row["worker_id"], [])
        workers.append(worker)
    return workers


# ── Time Logs ─────────────────────────────────────────────

def save_time_log(time_log: TimeLog):
    sheet = get_sheet("Time_Logs")
    sheet.append_row([
        time_log.worker_id,
        time_log.hours,
        ",".join(time_log.categories),
        time_log.description or "",
        time_log.date.strftime("%Y-%m-%d %H:%M:%S")
    ])