from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import db, User
from functools import wraps

users_bp = Blueprint("users", __name__, url_prefix="/users")


def manager_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_manager():
            flash("Manager access required", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


@users_bp.route("")
@login_required
@manager_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users/list.html", users=users)


@users_bp.route("/new", methods=["GET", "POST"])
@login_required
@manager_required
def new_user():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "cashier")
        if not email or not password:
            flash("Email and password are required", "danger")
            return render_template("users/new.html")
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "danger")
            return render_template("users/new.html")
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("User created", "success")
        return redirect(url_for("users.list_users"))
    return render_template("users/new.html")


@users_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@manager_required
def edit_user(user_id: int):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        role = request.form.get("role", user.role)
        password = request.form.get("password", "").strip()
        user.role = role
        if password:
            user.set_password(password)
        db.session.commit()
        flash("User updated", "success")
        return redirect(url_for("users.list_users"))
    return render_template("users/edit.html", user=user)