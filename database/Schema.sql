DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS customers CASCADE;


CREATE TABLE customers (
    customer_id   SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    city          VARCHAR(100),
    signup_date   DATE NOT NULL
);

CREATE TABLE employees (
    employee_id   SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    role          VARCHAR(50) NOT NULL,       
    department    VARCHAR(50) NOT NULL,      
    hire_date     DATE NOT NULL
);

CREATE TABLE products (
    product_id    SERIAL PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    category      VARCHAR(50) NOT NULL,      
    unit_price    NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE orders (
    order_id      SERIAL PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    employee_id   INTEGER NOT NULL REFERENCES employees(employee_id),
    order_date    DATE NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'completed', 'cancelled'))
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    subtotal      NUMERIC(10, 2) NOT NULL CHECK (subtotal >= 0)
);

-- =========================================================
-- Indexes on foreign keys and commonly filtered/joined columns.
-- Worth mentioning in an interview: without these, joins and
-- date-range filters on large tables would do full table scans.
-- =========================================================

CREATE INDEX idx_orders_customer_id   ON orders(customer_id);
CREATE INDEX idx_orders_employee_id   ON orders(employee_id);
CREATE INDEX idx_orders_order_date    ON orders(order_date);
CREATE INDEX idx_orders_status        ON orders(status);
CREATE INDEX idx_order_items_order_id   ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_products_category    ON products(category);