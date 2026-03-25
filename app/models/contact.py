from datetime import datetime


class RelatedPerson:
    """Represents a family member or related contact (mother, grandmother, etc.)"""
    def __init__(self, name, relationship, phone=None, address=None):
        self.name = name
        self.relationship = relationship  # e.g. "mother", "grandmother", "uncle"
        self.phone = phone
        self.address = address


class ContactAttempt:
    """Represents a single attempt to reach a contact"""
    def __init__(self, date, reached, reached_via, notes=None):
        self.date = date                  # datetime
        self.reached = reached            # bool
        self.reached_via = reached_via    # e.g. "self", "mother", "grandmother"
        self.notes = notes                # optional notes about the attempt


class Contact:
    def __init__(
        self,
        contact_id,
        name,
        date_of_birth,
        phone,
        address,
        referral_source,
        referral_date,
        referral_description,
        added_by,
        photo=None,
    ):
        # Basic info
        self.contact_id = contact_id
        self.name = name
        self.date_of_birth = date_of_birth
        self.phone = phone
        self.address = address

        # Referral info
        self.referral_source = referral_source        # e.g. "SBPD", "JJC", "walk-in"
        self.referral_date = referral_date            # datetime
        self.referral_description = referral_description
        self.photo = photo                            # file path or URL

        # Related people (mother, grandmother, etc.)
        self.related_people: list[RelatedPerson] = []

        # Contact attempt history
        self.contact_attempts: list[ContactAttempt] = []

        # Meta
        self.date_added = datetime.now()
        self.added_by = added_by                      # SocialWorker ID

    def add_related_person(self, name, relationship, phone=None, address=None):
        person = RelatedPerson(name, relationship, phone, address)
        self.related_people.append(person)

    def log_contact_attempt(self, reached, reached_via, notes=None):
        attempt = ContactAttempt(
            date=datetime.now(),
            reached=reached,
            reached_via=reached_via,
            notes=notes
        )
        self.contact_attempts.append(attempt)

    def was_reached(self):
        """Returns True if any attempt was successful"""
        return any(a.reached for a in self.contact_attempts)

    def __repr__(self):
        return f"<Contact {self.contact_id}: {self.name}>"