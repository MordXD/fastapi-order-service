

CREATE EXTENSION IF NOT EXISTS "ltree";

CREATE TABLE clients (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL
);


CREATE TABLE categories(
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    path LTREE NOT NULL,
    parent_id BIGINT REFERENCES categories(id) ON DELETE CASCADE,
    CONSTRAINT uq_categories_path UNIQUE(path),
    CONSTRAINT uq_categories_parent_name UNIQUE(parent_id, name)
);

CREATE INDEX idx_categories_path ON categories USING GIST(path);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);

CREATE TABLE products(
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(12,2) NOT NULL CHECK(price >= 0),
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE INDEX idx_products_category_id ON products(category_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'order_status'
    ) THEN
        CREATE TYPE order_status AS ENUM (
            'NEW', 'PROCESSING', 'COMPLETED', 'CANCELLED'
        );
    END IF;
END$$;

CREATE TABLE inventory(
    product_id BIGINT PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    stock INT NOT NULL CHECK(stock >= 0)
);


CREATE TABLE orders(
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status order_status NOT NULL DEFAULT 'NEW'
);

CREATE INDEX idx_orders_client_created ON orders(client_id, created_at);
CREATE INDEX idx_orders_status_created ON orders(status, created_at);

CREATE TABLE order_items(
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    qty INT NOT NULL CHECK(qty > 0),
    price_at_moment NUMERIC(12,2) NOT NULL CHECK(price_at_moment >= 0),
    amount NUMERIC(14,2) GENERATED ALWAYS AS (qty * price_at_moment) STORED,
    PRIMARY KEY(order_id, product_id)
);

CREATE INDEX idx_order_item_order ON order_items(order_id);
CREATE INDEX idx_order_item_product ON order_items(product_id);