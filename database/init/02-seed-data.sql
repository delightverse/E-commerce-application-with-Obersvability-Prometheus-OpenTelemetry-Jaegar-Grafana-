-- ============================================================================
-- E-Commerce Database Seed Data
-- ============================================================================
-- Tables already created by 01-create-schema.sql
-- Products can now be inserted!
-- ============================================================================


-- Insert Sample Products
INSERT INTO products (name, description, price, stock, created_at) VALUES
('iPhone 15 Pro', 'Latest Apple smartphone with A17 Pro chip and titanium design', 999.99, 50, NOW()),
('MacBook Pro M3', '14-inch laptop with M3 chip, 16GB RAM, 512GB SSD', 1999.99, 30, NOW()),
('AirPods Pro', 'Wireless earbuds with active noise cancellation', 249.99, 100, NOW()),
('iPad Air', '10.9-inch tablet with M1 chip and Apple Pencil support', 599.99, 75, NOW()),
('Apple Watch Series 9', 'Smartwatch with fitness tracking and health monitoring', 399.99, 60, NOW()),
('Magic Keyboard', 'Wireless keyboard with numeric keypad and Touch ID', 149.99, 80, NOW()),
('Magic Mouse', 'Wireless multi-touch mouse with rechargeable battery', 79.99, 120, NOW()),
('HomePod mini', 'Smart speaker with Siri and HomeKit integration', 99.99, 90, NOW()),
('Apple TV 4K', 'Streaming device with 4K HDR and Dolby Atmos', 179.99, 40, NOW()),
('AirTag 4 Pack', 'Item trackers for finding your belongings', 99.99, 150, NOW());

ON CONFLICT DO NOTHING;

-- Verify seeding
DO $$
DECLARE
    product_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO product_count FROM products;
    RAISE NOTICE '✅ Seeded % products successfully', product_count;
END $$;
-- Note: Orders will be created through the API to demonstrate observability features with real practice transactions.