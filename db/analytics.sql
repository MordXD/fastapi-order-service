-- =======================================
-- ДЕНОРМАЛИЗАЦИЯ: СЧЕТЧИКИ ПРОДАЖ
-- =======================================

ALTER TABLE products ADD COLUMN total_sold INT NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_products_total_sold ON products(total_sold DESC);


CREATE OR REPLACE FUNCTION update_product_sales_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE products SET total_sold = total_sold + NEW.qty WHERE id = NEW.product_id;
    ELSIF (TG_OP = 'UPDATE') THEN
        UPDATE products SET total_sold = total_sold + (NEW.qty - OLD.qty) WHERE id = NEW.product_id;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE products SET total_sold = total_sold - OLD.qty WHERE id = OLD.product_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS order_items_sales_trigger ON order_items;

CREATE TRIGGER order_items_sales_trigger

AFTER INSERT OR UPDATE OR DELETE ON order_items

FOR EACH ROW EXECUTE FUNCTION update_product_sales_count();



CREATE TABLE daily_product_sales (
    sale_date DATE NOT NULL,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    total_qty_sold INT NOT NULL,
    total_amount_sold NUMERIC(14,2) NOT NULL,
    PRIMARY KEY (sale_date, product_id)
);


CREATE OR REPLACE FUNCTION refresh_daily_sales(report_date DATE)
RETURNS void AS $$
BEGIN
    DELETE FROM daily_product_sales WHERE sale_date = report_date;

    INSERT INTO daily_product_sales (sale_date, product_id, total_qty_sold, total_amount_sold)
    SELECT
        o.created_at::date,
        oi.product_id,
        SUM(oi.qty) as total_qty_sold,
        SUM(oi.amount) as total_amount_sold
    FROM
        orders o
    JOIN
        order_items oi ON o.id = oi.order_id
    WHERE
        o.created_at::date = report_date
        AND o.status IN ('PROCESSING', 'COMPLETED') 
    GROUP BY
        o.created_at::date, oi.product_id;
END;
$$ LANGUAGE plpgsql;