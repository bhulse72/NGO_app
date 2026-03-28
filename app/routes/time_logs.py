from flask import Blueprint, request, jsonify
from app.services.sheets_service import save_time_log, load_all_social_workers
from app.models.time_log import TimeLog
from datetime import datetime

time_logs_bp = Blueprint("time_logs", __name__, url_prefix="/time_logs")


@time_logs_bp.route("/", methods=["GET"])
def list_time_logs():
    workers = load_all_social_workers()
    all_logs = []
    for worker in workers:
        for log in worker.time_logs:
            all_logs.append({
                "worker_id": log.worker_id,
                "hours": log.hours,
                "categories": log.categories,
                "description": log.description,
                "date": log.date.strftime("%Y-%m-%d")
            })
    # Sort most recent first
    all_logs.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(all_logs)


@time_logs_bp.route("/<worker_id>", methods=["GET"])
def get_worker_logs(worker_id):
    workers = load_all_social_workers()
    worker = next((w for w in workers if w.worker_id == worker_id), None)
    if not worker:
        return jsonify({"error": "Social worker not found"}), 404
    logs = sorted(worker.time_logs, key=lambda l: l.date, reverse=True)
    return jsonify({
        "worker_id": worker.worker_id,
        "name": worker.name,
        "total_hours": sum(l.hours for l in logs),
        "hours_by_category": worker.get_hours_by_category(),
        "logs": [{
            "hours": l.hours,
            "categories": l.categories,
            "description": l.description,
            "date": l.date.strftime("%Y-%m-%d")
        } for l in logs]
    })


@time_logs_bp.route("/", methods=["POST"])
def add_time_log():
    data = request.get_json()

    if not data.get("worker_id"):
        return jsonify({"error": "worker_id is required"}), 400
    if not data.get("hours"):
        return jsonify({"error": "hours is required"}), 400
    if not data.get("categories"):
        return jsonify({"error": "at least one category is required"}), 400

    log = TimeLog(
        worker_id=data["worker_id"],
        hours=float(data["hours"]),
        categories=data["categories"],  # expects a list
        description=data.get("description"),
        date=datetime.strptime(data["date"], "%Y-%m-%d") if data.get("date") else None
    )
    save_time_log(log)
    return jsonify({"message": "Time log added successfully"}), 201


@time_logs_bp.route("/categories", methods=["GET"])
def list_categories():
    return jsonify({"categories": TimeLog.DEFAULT_CATEGORIES})