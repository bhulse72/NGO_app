from flask import Blueprint, request, jsonify
from app.services.sheets_service import save_social_worker, load_all_social_workers
from app.models.social_worker import SocialWorker

social_workers_bp = Blueprint("social_workers", __name__, url_prefix="/social_workers")


@social_workers_bp.route("/", methods=["GET"])
def list_social_workers():
    workers = load_all_social_workers()
    return jsonify([{
        "worker_id": w.worker_id,
        "name": w.name,
        "email": w.email,
        "is_admin": w.is_admin,
        "assigned_clients": w.assigned_clients
    } for w in workers])


@social_workers_bp.route("/<worker_id>", methods=["GET"])
def get_social_worker(worker_id):
    workers = load_all_social_workers()
    worker = next((w for w in workers if w.worker_id == worker_id), None)
    if not worker:
        return jsonify({"error": "Social worker not found"}), 404
    return jsonify({
        "worker_id": worker.worker_id,
        "name": worker.name,
        "email": worker.email,
        "is_admin": worker.is_admin,
        "assigned_clients": worker.assigned_clients,
        "hours_by_category": worker.get_hours_by_category()
    })


@social_workers_bp.route("/", methods=["POST"])
def add_social_worker():
    data = request.get_json()
    workers = load_all_social_workers()

    # Check for duplicate worker_id or email
    if any(w.worker_id == data["worker_id"] for w in workers):
        return jsonify({"error": "Worker ID already exists"}), 409
    if any(w.email == data["email"] for w in workers):
        return jsonify({"error": "Email already registered"}), 409

    worker = SocialWorker(
        worker_id=data["worker_id"],
        name=data["name"],
        email=data["email"],
        is_admin=data.get("is_admin", False)
    )
    save_social_worker(worker)
    return jsonify({"message": "Social worker added successfully", "worker_id": worker.worker_id}), 201


@social_workers_bp.route("/<worker_id>/assign", methods=["PATCH"])
def assign_client(worker_id):
    data = request.get_json()
    workers = load_all_social_workers()
    worker = next((w for w in workers if w.worker_id == worker_id), None)
    if not worker:
        return jsonify({"error": "Social worker not found"}), 404

    client_id = data.get("client_id")
    if not client_id:
        return jsonify({"error": "client_id is required"}), 400

    worker.assign_client(client_id)
    save_social_worker(worker)
    return jsonify({"message": f"Client {client_id} assigned to {worker.name}", "assigned_clients": worker.assigned_clients})


@social_workers_bp.route("/<worker_id>/unassign", methods=["PATCH"])
def unassign_client(worker_id):
    data = request.get_json()
    workers = load_all_social_workers()
    worker = next((w for w in workers if w.worker_id == worker_id), None)
    if not worker:
        return jsonify({"error": "Social worker not found"}), 404

    client_id = data.get("client_id")
    if not client_id:
        return jsonify({"error": "client_id is required"}), 400

    worker.unassign_client(client_id)
    save_social_worker(worker)
    return jsonify({"message": f"Client {client_id} unassigned from {worker.name}", "assigned_clients": worker.assigned_clients})