from datetime import datetime
from app.models.contact import Contact, RelatedPerson
from app.models.client import Client
from app.models.note import Note
from app.models.social_worker import SocialWorker
from app.models.time_log import TimeLog


# --- Social Workers ---
worker1 = SocialWorker(
    worker_id="sw001",
    name="Maria Garcia",
    email="maria@ngo.org",
    is_admin=True
)

worker2 = SocialWorker(
    worker_id="sw002",
    name="James Brown",
    email="james@ngo.org",
    is_admin=False
)


# --- Contacts ---
contact1 = Contact(
    contact_id="c001",
    name="Marcus Johnson",
    date_of_birth=datetime(2005, 3, 14),
    phone="555-1234",
    address="123 Oak St, South Bend, IN",
    referral_source="SBPD",
    referral_date=datetime(2024, 1, 10),
    referral_description="Referred by police after altercation near school.",
    added_by="sw001"
)
contact1.add_related_person("Linda Johnson", "mother", "555-5678", "123 Oak St, South Bend, IN")
contact1.add_related_person("Dorothy Johnson", "grandmother", "555-9999", "456 Elm St, South Bend, IN")
contact1.log_contact_attempt(reached=False, reached_via="self", notes="No answer on phone")
contact1.log_contact_attempt(reached=True, reached_via="mother", notes="Mother confirmed address")


contact2 = Contact(
    contact_id="c002",
    name="Darius Williams",
    date_of_birth=datetime(2003, 7, 22),
    phone="555-4321",
    address="789 Maple Ave, South Bend, IN",
    referral_source="JJC",
    referral_date=datetime(2024, 2, 5),
    referral_description="Referred by Juvenile Justice Center after probation violation.",
    added_by="sw002"
)
contact2.add_related_person("Sharon Williams", "mother", "555-8765")
contact2.log_contact_attempt(reached=True, reached_via="self", notes="Spoke directly, agreed to meet")


# --- Clients ---
note1 = Note(
    author="sw001",
    text="Initial meeting went well. Marcus is open to career counseling.",
)
note2 = Note(
    author="sw001",
    text="Follow up meeting. Discussed school re-enrollment options.",
)

client1 = Client(
    contact_id="cl001",
    name="Trevor Davis",
    date_of_birth=datetime(2004, 11, 2),
    phone="555-1111",
    address="321 Pine St, South Bend, IN",
    referral_source="Walk-in",
    referral_date=datetime(2024, 1, 20),
    referral_description="Walked in requesting help with housing and employment.",
    added_by="sw001",
    assigned_to="sw001",
    inactivity_days=90
)
client1.set_risk_level("Low risk")
client1.add_note(note1)
client1.add_note(note2)
client1.add_related_person("Barbara Davis", "mother", "555-2222")


# --- Time Logs ---
log1 = TimeLog(
    worker_id="sw001",
    hours=2.0,
    categories=["Establishing Contact", "Mental Health Help"],
    description="Initial outreach and assessment for Trevor Davis",
    date=datetime(2024, 3, 1)
)

log2 = TimeLog(
    worker_id="sw002",
    hours=1.5,
    categories=["Career Counseling"],
    description="Career options discussion with Darius Williams",
    date=datetime(2024, 3, 3)
)

worker1.assign_client("cl001")
worker1.log_time(log1)
worker2.log_time(log2)


# --- Easy access ---
all_contacts = [contact1, contact2]
all_clients = [client1]
all_workers = [worker1, worker2]