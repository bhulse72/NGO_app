from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
from config import USERS

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET"])
def login_page():
    if session.get("username"):
        return redirect(url_for("index"))
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    user = USERS.get(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["username"] = username
    return jsonify({"message": "Logged in", "name": user["name"]}), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))