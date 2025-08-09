from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from .models import db, Product, Sale, SaleItem

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal("0.00")


@sales_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_sale():
    products = Product.query.order_by(Product.name.asc()).all()
    if request.method == "POST":
        product_ids = request.form.getlist("product_id")
        quantities = request.form.getlist("quantity")
        paid_amount = _to_decimal(request.form.get("paid_amount", "0"))

        items = []
        total = Decimal("0.00")
        for pid, qty_str in zip(product_ids, quantities):
            try:
                qty = int(qty_str or 0)
            except Exception:
                qty = 0
            if qty <= 0:
                continue
            product = Product.query.get(int(pid))
            if not product:
                continue
            unit_price = Decimal(str(product.price))
            line_total = (unit_price * qty).quantize(Decimal("0.01"))
            total += line_total
            items.append({
                "product": product,
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            })

        if total <= 0:
            flash("Please add at least one item with quantity.", "danger")
            return render_template("sales/new_sale.html", products=products)

        change_amount = (paid_amount - total).quantize(Decimal("0.01"))
        if paid_amount < total:
            flash("Paid amount is less than total. Please collect full payment.", "danger")
            return render_template("sales/new_sale.html", products=products, total=str(total), paid_amount=str(paid_amount))

        sale = Sale(user_id=current_user.id, total_amount=total, paid_amount=paid_amount, change_amount=change_amount)
        db.session.add(sale)
        db.session.flush()

        for item in items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item["product"].id,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                line_total=item["line_total"],
            )
            db.session.add(sale_item)
        db.session.commit()

        flash(f"Sale saved. Change: {change_amount}", "success")
        return redirect(url_for("sales.list_sales"))

    return render_template("sales/new_sale.html", products=products)


@sales_bp.route("/list")
@login_required
def list_sales():
    sales = (
        db.session.query(Sale)
        .order_by(Sale.created_at.desc())
        .limit(100)
        .all()
    )
    return render_template("sales/list.html", sales=sales)


@sales_bp.route("/reports")
@login_required
def reports():
    range_key = request.args.get("range", "today")
    now = datetime.utcnow()

    if range_key == "week":
        start = now - timedelta(days=7)
    elif range_key == "month":
        start = now - timedelta(days=30)
    elif range_key == "year":
        start = now - timedelta(days=365)
    else:
        start = datetime(now.year, now.month, now.day)

    # Daily total sales (sum per day)
    daily_totals = (
        db.session.query(
            func.date(Sale.created_at).label("day"),
            func.sum(Sale.total_amount).label("total")
        )
        .filter(Sale.created_at >= start)
        .group_by(func.date(Sale.created_at))
        .order_by(func.date(Sale.created_at).asc())
        .all()
    )

    # Product totals within range
    product_totals = (
        db.session.query(
            Product.name.label("product_name"),
            func.sum(SaleItem.quantity).label("total_qty"),
            func.sum(SaleItem.line_total).label("total_amount"),
        )
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Sale.created_at >= start)
        .group_by(Product.name)
        .order_by(Product.name.asc())
        .all()
    )

    # Overall total
    overall_total = (
        db.session.query(func.sum(Sale.total_amount))
        .filter(Sale.created_at >= start)
        .scalar()
    ) or 0

    return render_template(
        "sales/report.html",
        range_key=range_key,
        daily_totals=daily_totals,
        product_totals=product_totals,
        overall_total=overall_total,
    )