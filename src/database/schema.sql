-- ============================================
-- Customers
-- ============================================

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================
-- Invoices
-- ============================================

CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,

    invoice_number VARCHAR(100) UNIQUE NOT NULL,

    customer_id INTEGER NOT NULL,

    invoice_date DATE NOT NULL,

    subtotal NUMERIC(12, 2) NOT NULL,
    gst NUMERIC(12, 2) NOT NULL,
    total NUMERIC(12, 2) NOT NULL,

    status VARCHAR(50) NOT NULL
        CHECK (status IN ('paid', 'unpaid', 'partially_paid')),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Each invoice belongs to one customer.
    FOREIGN KEY (customer_id)
        REFERENCES customers(id)
);


-- ============================================
-- Invoice Items
-- ============================================

CREATE TABLE IF NOT EXISTS invoice_items (
    id SERIAL PRIMARY KEY,

    invoice_id INTEGER NOT NULL,

    description VARCHAR(500) NOT NULL,

    quantity NUMERIC(10, 2) NOT NULL,

    unit_price NUMERIC(12, 2) NOT NULL,

    amount NUMERIC(12, 2) NOT NULL,

    -- Each item belongs to an invoice.
    FOREIGN KEY (invoice_id)
        REFERENCES invoices(id)
        ON DELETE CASCADE
);


-- ============================================
-- Payments
-- ============================================

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,

    invoice_id INTEGER NOT NULL,

    payment_date DATE NOT NULL,

    amount NUMERIC(12, 2) NOT NULL,

    payment_method VARCHAR(50),

    -- Each payment belongs to an invoice.
    FOREIGN KEY (invoice_id)
        REFERENCES invoices(id)
        ON DELETE CASCADE
);