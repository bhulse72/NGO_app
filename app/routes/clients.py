from flask import Blueprint, request, jsonify, render_template
from app.services.sheets_service import save_client, load_all_clients
from app.models.client import Client
from app.models.note import Note
from datetime import datetime

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.route("/", methods=["GET"])
def list_clients():
    clients = load_all_clients()
    if request.headers.get("Accept", "").startswith("application/json") or request.args.get("format") == "json":
        return jsonify([{
            "contact_id": c.contact_id,
            "name": c.name,
            "phone": c.phone,
            "address": c.address,
            "referral_source": c.referral_source,
            "assigned_to": c.assigned_to,
            "risk_level": c.risk_level,
            "is_active": c.is_active,
            "client_since": c.client_since.strftime("%Y-%m-%d") if c.client_since else None
        } for c in clients])
    return render_template("clients/list.html", clients=clients)


@clients_bp.route("/<contact_id>", methods=["GET"])
def get_client(contact_id):
    clients = load_all_clients()
    client = next((c for c in clients if c.contact_id == contact_id), None)
    if not client:
        if request.headers.get("Accept", "").startswith("application/json"):
            return jsonify({"error": "Client not found"}), 404
        return render_template("404.html"), 404
    if request.headers.get("Accept", "").startswith("application/json") or request.args.get("format") == "json":
        return jsonify({
            "contact_id": client.contact_id,
            "name": client.name,
            "date_of_birth": client.date_of_birth.strftime("%Y-%m-%d") if client.date_of_birth else None,
            "phone": client.phone,
            "address": client.address,
            "referral_source": client.referral_source,
            "referral_description": client.referral_description,
            "assigned_to": client.assigned_to,
            "risk_level": client.risk_level,
            "is_active": client.is_active,
            "inactivity_days": client.inactivity_days,
            "client_since": client.client_since.strftime("%Y-%m-%d") if client.client_since else None,
            "last_activity_date": client.last_activity_date.strftime("%Y-%m-%d") if client.last_activity_date else None,
            "was_reached": client.was_reached(),
            "notes": [{"author": n.author, "text": n.text, "attachments": n.attachments, "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S")} for n in client.get_notes()],
            "related_people": [{"name": p.name, "relationship": p.relationship, "phone": p.phone, "address": p.address} for p in client.related_people]
        })
    return render_template("clients/detail.html", client=client)


@clients_bp.route("/", methods=["POST"])
def add_client():
    data = request.get_json()
    existing = load_all_clients()
    similar = [c.name for c in existing if data["name"].lower() in c.name.lower() or c.name.lower() in data["name"].lower()]
    if similar:
        return jsonify({"warning": "Similar clients already exist", "similar_names": similar}), 409
    client = Client(
        contact_id=data["contact_id"],
        name=data["name"],
        date_of_birth=datetime.strptime(data["date_of_birth"], "%Y-%m-%d") if data.get("date_of_birth") else None,
        phone=data.get("phone"),
        address=data.get("address"),
        referral_source=data.get("referral_source"),
        referral_date=datetime.strptime(data["referral_date"], "%Y-%m-%d") if data.get("referral_date") else None,
        referral_description=data.get("referral_description"),
        added_by=data.get("added_by"),
        assigned_to=data.get("assigned_to"),
        inactivity_days=data.get("inactivity_days", 90)
    )
    save_client(client)
    return jsonify({"message": "Client added successfully", "contact_id": client.contact_id}), 201


@clients_bp.route("/<contact_id>/risk", methods=["PATCH"])
def update_risk_level(contact_id):
    data = request.get_json()
    clients = load_all_clients()
    client = next((c for c in clients if c.contact_id == contact_id), None)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    try:
        client.set_risk_level(data["risk_level"])
        save_client(client)
        return jsonify({"message": "Risk level updated", "risk_level": client.risk_level})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@clients_bp.route("/<contact_id>/notes", methods=["POST"])
def add_note(contact_id):
    data = request.get_json()
    clients = load_all_clients()
    client = next((c for c in clients if c.contact_id == contact_id), None)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    note = Note(author=data["author"], text=data["text"], attachments=data.get("attachments", []))
    client.add_note(note)
    save_client(client)
    return jsonify({"message": "Note added successfully"}), 201