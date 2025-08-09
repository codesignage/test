from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import db, Product
from functools import wraps

products_bp = Blueprint("products", __name__, url_prefix="/products")


def manager_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "manager":
            flash("Manager access required", "danger")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


@products_bp.route("")
@login_required
@manager_required
def list_products():
    products = Product.query.order_by(Product.name.asc()).all()
    return render_template("products/list.html", products=products)


@products_bp.route("/new", methods=["GET", "POST"])
@login_required
@manager_required
def new_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price_str = request.form.get("price", "0").strip()
        if not name:
            flash("Name is required", "danger")
            return render_template("products/new.html")
        try:
            price = round(float(price_str), 2)
        except Exception:
            flash("Invalid price", "danger")
            return render_template("products/new.html")
        if Product.query.filter_by(name=name).first():
            flash("Product with this name already exists", "danger")
            return render_template("products/new.html")
        product = Product(name=name, price=price)
        db.session.add(product)
        db.session.commit()
        flash("Product created", "success")
        return redirect(url_for("products.list_products"))
    return render_template("products/new.html")