import os
from datetime import datetime, timedelta
from random import randint, seed as rand_seed
from decimal import Decimal

from flask import Flask

from .app import create_app
from .models import db, User, Product, Sale, SaleItem


def seed_data():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Users
        manager_email = os.environ.get("MANAGER_EMAIL", "manager@example.com").strip().lower()
        manager_password = os.environ.get("MANAGER_PASSWORD", "password123")
        manager = User.query.filter_by(email=manager_email).first()
        if not manager:
            manager = User(email=manager_email, role="manager")
            manager.set_password(manager_password)
            db.session.add(manager)
            print(f"Created manager: {manager_email} / {manager_password}")

        for email in ["alice@example.com", "bob@example.com"]:
            if not User.query.filter_by(email=email).first():
                u = User(email=email, role="cashier")
                u.set_password("password123")
                db.session.add(u)
                print(f"Created cashier: {email} / password123")

        # Products
        products_spec = [
            ("Coffee", Decimal("2.50")),
            ("Tea", Decimal("2.00")),
            ("Sandwich", Decimal("5.00")),
            ("Cake", Decimal("3.75")),
            ("Juice", Decimal("2.25")),
        ]
        products = []
        for name, price in products_spec:
            p = Product.query.filter_by(name=name).first()
            if not p:
                p = Product(name=name, price=price)
                db.session.add(p)
            products.append(p)

        db.session.commit()

        # Sales sample (past 14 days)
        rand_seed(42)
        users = User.query.all()
        for day_offset in range(14, -1, -1):
            day = datetime.utcnow() - timedelta(days=day_offset)
            # 3-8 sales per day
            for _ in range(randint(3, 8)):
                user = users[randint(0, len(users)-1)]
                num_items = randint(1, 4)
                total = Decimal("0.00")
                sale = Sale(user_id=user.id, total_amount=0, paid_amount=0, change_amount=0, created_at=day)
                db.session.add(sale)
                db.session.flush()
                for _ in range(num_items):
                    product = products[randint(0, len(products)-1)]
                    qty = randint(1, 3)
                    unit_price = Decimal(str(product.price))
                    line_total = unit_price * qty
                    total += line_total
                    item = SaleItem(
                        sale_id=sale.id,
                        product_id=product.id,
                        quantity=qty,
                        unit_price=unit_price,
                        line_total=line_total,
                        created_at=day,
                    )
                    db.session.add(item)
                paid = total
                change = Decimal("0.00")
                sale.total_amount = total
                sale.paid_amount = paid
                sale.change_amount = change
        db.session.commit()
        print("Seeding complete.")


if __name__ == "__main__":
    seed_data()