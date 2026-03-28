from flask import Blueprint, request, jsonify, render_template
from app.services.sheets_service import save_contact, load_all_contacts
from app.models.contact import Contact
from datetime import datetime

contacts_bp = Blueprint("contacts", __name__, url_prefix="/contacts")


@contacts_bp.route("/", methods=["GET"])
def list_contacts():
    # Return HTML page if browser request, JSON if API request
    contacts = load_all_contacts()
    if request.headers.get("Accept", "").startswith("application/json") or request.args.get("format") == "json":
        return jsonify([{
            "contact_id": c.contact_id,
            "name": c.name,
            "phone": c.phone,
            "address": c.address,
            "referral_source": c.referral_source,
            "referral_date": c.referral_date.strftime("%Y-%m-%d") if c.referral_date else None,
            "was_reached": c.was_reached()
        } for c in contacts])
    return render_template("contacts/list.html", contacts=contacts)


@contacts_bp.route("/<contact_id>", methods=["GET"])
def get_contact(contact_id):
    contacts = load_all_contacts()
    contact = next((c for c in contacts if c.contact_id == contact_id), None)
    if not contact:
        if request.headers.get("Accept", "").startswith("application/json"):
            return jsonify({"error": "Contact not found"}), 404
        return render_template("404.html"), 404
    if request.headers.get("Accept", "").startswith("application/json") or request.args.get("format") == "json":
        return jsonify({
            "contact_id": contact.contact_id,
            "name": contact.name,
            "date_of_birth": contact.date_of_birth.strftime("%Y-%m-%d") if contact.date_of_birth else None,
            "phone": contact.phone,
            "address": contact.address,
            "referral_source": contact.referral_source,
            "referral_date": contact.referral_date.strftime("%Y-%m-%d") if contact.referral_date else None,
            "referral_description": contact.referral_description,
            "added_by": contact.added_by,
            "date_added": contact.date_added.strftime("%Y-%m-%d %H:%M:%S"),
            "was_reached": contact.was_reached(),
            "related_people": [{"name": p.name, "relationship": p.relationship, "phone": p.phone, "address": p.address} for p in contact.related_people],
            "contact_attempts": [{"date": a.date.strftime("%Y-%m-%d %H:%M:%S"), "reached": a.reached, "reached_via": a.reached_via, "notes": a.notes} for a in contact.contact_attempts]
        })
    return render_template("contacts/detail.html", contact=contact)


@contacts_bp.route("/", methods=["POST"])
def add_contact():
    data = request.get_json()
    existing = load_all_contacts()
    similar = [c.name for c in existing if data["name"].lower() in c.name.lower() or c.name.lower() in data["name"].lower()]
    if similar:
        return jsonify({"warning": "Similar contacts already exist", "similar_names": similar}), 409

    contact = Contact(
        contact_id=data["contact_id"],
        name=data["name"],
        date_of_birth=datetime.strptime(data["date_of_birth"], "%Y-%m-%d") if data.get("date_of_birth") else None,
        phone=data.get("phone"),
        address=data.get("address"),
        referral_source=data.get("referral_source"),
        referral_date=datetime.strptime(data["referral_date"], "%Y-%m-%d") if data.get("referral_date") else None,
        referral_description=data.get("referral_description"),
        added_by=data.get("added_by"),
        photo=data.get("photo")
    )

    # Add related people from payload
    for rp in data.get("related_people", []):
        contact.add_related_person(
            name=rp["name"],
            relationship=rp["relationship"],
            phone=rp.get("phone"),
            address=rp.get("address")
        )

    save_contact(contact)
    return jsonify({"message": "Contact added successfully", "contact_id": contact.contact_id}), 201

@contacts_bp.route("/new", methods=["GET"])
def new_contact():
    from app.services.sheets_service import load_all_social_workers
    workers = load_all_social_workers()
    return render_template("contacts/new.html", workers=workers)