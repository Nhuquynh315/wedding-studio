import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db, limiter
from app.models import User

auth_bp = Blueprint("auth", __name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("wedding.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([full_name, email, password, confirm_password]):
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if not _EMAIL_RE.match(email):
            flash("Please enter a valid email address.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html")

        user = User(full_name=full_name, email=email)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Something went wrong creating your account. Please try again.", "danger")
            return render_template("auth/register.html")

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("20 per minute; 5 per second")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("wedding.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("wedding.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("wedding.dashboard"))
