"""
Generates synthetic data and inserts it into the database.
Run this AFTER run_schema.py has created the tables.

Usage: python database/seed_data.py
"""

import os
import random
from datetime import date

import psycopg2
from dotenv import load_dotenv
from faker import Faker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from your .env file.")

fake = Faker()
Faker.seed(42)     
random.seed(42)

# row counts 
NUM_CUSTOMERS = 200
NUM_EMPLOYEES = 25
NUM_PRODUCTS = 100
NUM_ORDERS = 600
MAX_ITEMS_PER_ORDER = 4


EMPLOYEE_ROLES = ["Sales Rep", "Account Manager", "Support Agent", "Team Lead"]
DEPARTMENTS = ["Sales", "Support", "Marketing"]
PRODUCT_CATEGORIES = ["Electronics", "Furniture", "Office Supplies", "Apparel", "Home Goods"]
ORDER_STATUSES = ["completed", "pending", "cancelled"]
ORDER_STATUS_WEIGHTS = [0.7, 0.2, 0.1]
ORDER_DATE_START = date(2023, 1, 1)
ORDER_DATE_END = date(2026, 9, 30)


def connect():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def seed_customers(cur) -> list[int]:
    ids = []
    for _ in range(NUM_CUSTOMERS):
        cur.execute(
            """
            INSERT INTO customers (name, email, city, signup_date)
            VALUES (%s, %s, %s, %s)
            RETURNING customer_id
            """,
            (
                fake.name(),
                fake.unique.email(),
                fake.city(),
                fake.date_between(start_date="-3y", end_date="today"),
            ),
        )
        ids.append(cur.fetchone()[0])
    return ids


def seed_employees(cur) -> list[int]:
    ids = []
    for _ in range(NUM_EMPLOYEES):
        cur.execute(
            """
            INSERT INTO employees (name, role, department, hire_date)
            VALUES (%s, %s, %s, %s)
            RETURNING employee_id
            """,
            (
                fake.name(),
                random.choice(EMPLOYEE_ROLES),
                random.choice(DEPARTMENTS),
                fake.date_between(start_date="-5y", end_date="-1y"),
            ),
        )
        ids.append(cur.fetchone()[0])
    return ids


def seed_products(cur) -> list[tuple[int, float]]:
    """Returns (product_id, unit_price) pairs, needed later to compute order_items subtotals."""
    products = []
    for _ in range(NUM_PRODUCTS):
        unit_price = round(random.uniform(5, 500), 2)
        cur.execute(
            """
            INSERT INTO products (name, category, unit_price)
            VALUES (%s, %s, %s)
            RETURNING product_id
            """,
            (
                fake.unique.catch_phrase(),
                random.choice(PRODUCT_CATEGORIES),
                unit_price,
            ),
        )
        product_id = cur.fetchone()[0]
        products.append((product_id, unit_price))
    return products


def seed_orders(cur, customer_ids: list[int], employee_ids: list[int]) -> list[int]:
    ids = []
    for _ in range(NUM_ORDERS):
        cur.execute(
            """
            INSERT INTO orders (customer_id, employee_id, order_date, status)
            VALUES (%s, %s, %s, %s)
            RETURNING order_id
            """,
            (
                random.choice(customer_ids),
                random.choice(employee_ids),
                fake.date_between(start_date=ORDER_DATE_START, end_date=ORDER_DATE_END),
                random.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS, k=1)[0],
            ),
        )
        ids.append(cur.fetchone()[0])
    return ids


def seed_order_items(cur, order_ids: list[int], products: list[tuple[int, float]]):
    rows_inserted = 0
    for order_id in order_ids:
        num_items = random.randint(1, MAX_ITEMS_PER_ORDER)
        chosen_products = random.sample(products, k=min(num_items, len(products)))

        for product_id, unit_price in chosen_products:
            quantity = random.randint(1, 5)
            subtotal = round(unit_price * quantity, 2)

            cur.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, subtotal)
                VALUES (%s, %s, %s, %s)
                """,
                (order_id, product_id, quantity, subtotal),
            )
            rows_inserted += 1
    return rows_inserted


def main():
    conn = connect()
    cur = conn.cursor()

    print("Seeding customers...")
    customer_ids = seed_customers(cur)
    print(f"  Inserted {len(customer_ids)} customers.")

    print("Seeding employees...")
    employee_ids = seed_employees(cur)
    print(f"  Inserted {len(employee_ids)} employees.")

    print("Seeding products...")
    products = seed_products(cur)
    print(f"  Inserted {len(products)} products.")

    print("Seeding orders...")
    order_ids = seed_orders(cur, customer_ids, employee_ids)
    print(f"  Inserted {len(order_ids)} orders.")

    print("Seeding order_items...")
    item_count = seed_order_items(cur, order_ids, products)
    print(f"  Inserted {item_count} order_items.")

    cur.close()
    conn.close()
    print("\nDone. Database is seeded and ready to query.")


if __name__ == "__main__":
    main()