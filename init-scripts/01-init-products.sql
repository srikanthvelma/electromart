-- Initialize ElectroMart Product Database
-- This script creates sample electronics products

-- Create databases if they don't exist
CREATE DATABASE IF NOT EXISTS electromart_products;
CREATE DATABASE IF NOT EXISTS electromart_orders;

-- Connect to products database
\c electromart_products;

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create brands table
CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    logo_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    category_id INTEGER REFERENCES categories(id),
    brand_id INTEGER REFERENCES brands(id),
    image_url VARCHAR(255),
    specifications JSONB,
    rating DECIMAL(3,2) DEFAULT 0.0,
    review_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample categories
INSERT INTO categories (name, description) VALUES
('Smartphones', 'Latest smartphones and mobile devices'),
('Laptops', 'High-performance laptops and notebooks'),
('Tablets', 'Tablets and iPads for work and entertainment'),
('Smart Watches', 'Smart watches and fitness trackers'),
('Headphones', 'Wireless and wired headphones'),
('Gaming Consoles', 'Gaming consoles and accessories')
ON CONFLICT (name) DO NOTHING;

-- Insert sample brands
INSERT INTO brands (name, description, logo_url) VALUES
('Apple', 'Think Different', 'https://example.com/apple-logo.png'),
('Samsung', 'Do What You Can''t', 'https://example.com/samsung-logo.png'),
('Google', 'Don''t Be Evil', 'https://example.com/google-logo.png'),
('Dell', 'The Power To Do More', 'https://example.com/dell-logo.png'),
('HP', 'Keep Reinventing', 'https://example.com/hp-logo.png'),
('Lenovo', 'For Those Who Do', 'https://example.com/lenovo-logo.png'),
('Sony', 'Make.Believe', 'https://example.com/sony-logo.png'),
('Bose', 'Better Sound Through Research', 'https://example.com/bose-logo.png'),
('Microsoft', 'Be What''s Next', 'https://example.com/microsoft-logo.png'),
('Nintendo', 'Playing is believing', 'https://example.com/nintendo-logo.png')
ON CONFLICT (name) DO NOTHING;

-- Insert sample products
INSERT INTO products (name, description, price, stock_quantity, category_id, brand_id, image_url, specifications, rating, review_count) VALUES
-- Smartphones
('iPhone 15 Pro', 'Latest iPhone with A17 Pro chip, titanium design, and advanced camera system', 999.99, 50, 1, 1, 'https://example.com/iphone15pro.jpg', '{"storage": "128GB", "color": "Natural Titanium", "screen": "6.1 inch", "camera": "48MP"}', 4.8, 1250),
('Samsung Galaxy S24 Ultra', 'Premium Android flagship with S Pen, 200MP camera, and AI features', 1199.99, 45, 1, 2, 'https://example.com/galaxys24ultra.jpg', '{"storage": "256GB", "color": "Titanium Gray", "screen": "6.8 inch", "camera": "200MP"}', 4.7, 980),
('Google Pixel 8 Pro', 'Google''s flagship with advanced AI and exceptional camera performance', 899.99, 30, 1, 3, 'https://example.com/pixel8pro.jpg', '{"storage": "128GB", "color": "Obsidian", "screen": "6.7 inch", "camera": "50MP"}', 4.6, 750),

-- Laptops
('MacBook Pro 16" M3 Max', 'Professional laptop with M3 Max chip for intensive workloads', 3499.99, 25, 2, 1, 'https://example.com/macbookpro16.jpg', '{"storage": "1TB", "ram": "32GB", "processor": "M3 Max", "display": "16 inch"}', 4.9, 450),
('Dell XPS 15', 'Premium Windows laptop with OLED display and powerful performance', 1899.99, 35, 2, 4, 'https://example.com/dellxps15.jpg', '{"storage": "512GB", "ram": "16GB", "processor": "Intel i7", "display": "15.6 inch"}', 4.7, 620),
('HP Spectre x360', 'Convertible laptop with premium design and long battery life', 1499.99, 40, 2, 5, 'https://example.com/hpspectre.jpg', '{"storage": "1TB", "ram": "16GB", "processor": "Intel i7", "display": "13.5 inch"}', 4.6, 380),
('Lenovo ThinkPad X1 Carbon', 'Business laptop with legendary keyboard and durability', 1699.99, 30, 2, 6, 'https://example.com/thinkpadx1.jpg', '{"storage": "512GB", "ram": "16GB", "processor": "Intel i7", "display": "14 inch"}', 4.8, 520),

-- Tablets
('iPad Pro 12.9" M2', 'Professional tablet with M2 chip and Liquid Retina XDR display', 1099.99, 60, 3, 1, 'https://example.com/ipadpro12.jpg', '{"storage": "256GB", "display": "12.9 inch", "processor": "M2", "cellular": false}', 4.8, 890),
('Samsung Galaxy Tab S9 Ultra', 'Android tablet with S Pen and large AMOLED display', 999.99, 45, 3, 2, 'https://example.com/galaxytabs9.jpg', '{"storage": "256GB", "display": "14.6 inch", "ram": "12GB", "cellular": true}', 4.7, 650),

-- Smart Watches
('Apple Watch Series 9', 'Latest Apple Watch with advanced health features and S9 chip', 399.99, 80, 4, 1, 'https://example.com/applewatch9.jpg', '{"size": "45mm", "case": "Aluminum", "band": "Sport Band", "cellular": false}', 4.8, 1200),
('Samsung Galaxy Watch 6', 'Android smartwatch with rotating bezel and health tracking', 349.99, 70, 4, 2, 'https://example.com/galaxywatch6.jpg', '{"size": "44mm", "case": "Aluminum", "display": "AMOLED", "battery": "425mAh"}', 4.6, 850),

-- Headphones
('AirPods Pro 2', 'Wireless earbuds with active noise cancellation and spatial audio', 249.99, 100, 5, 1, 'https://example.com/airpodspro2.jpg', '{"type": "Wireless", "noise_cancellation": true, "water_resistant": true, "battery": "6 hours"}', 4.7, 2100),
('Sony WH-1000XM5', 'Premium over-ear headphones with industry-leading noise cancellation', 399.99, 55, 5, 7, 'https://example.com/sonywh1000xm5.jpg', '{"type": "Over-ear", "noise_cancellation": true, "battery": "30 hours", "bluetooth": "5.2"}', 4.9, 1800),
('Bose QuietComfort 45', 'Comfortable headphones with excellent noise cancellation', 329.99, 65, 5, 8, 'https://example.com/boseqc45.jpg', '{"type": "Over-ear", "noise_cancellation": true, "battery": "24 hours", "comfort": "Excellent"}', 4.8, 950),

-- Gaming Consoles
('PlayStation 5', 'Next-gen gaming console with 4K graphics and fast loading', 499.99, 20, 6, 7, 'https://example.com/ps5.jpg', '{"storage": "825GB", "resolution": "4K", "ray_tracing": true, "backward_compatible": true}', 4.9, 3200),
('Xbox Series X', 'Microsoft''s most powerful console with Game Pass', 499.99, 25, 6, 9, 'https://example.com/xboxseriesx.jpg', '{"storage": "1TB", "resolution": "4K", "ray_tracing": true, "game_pass": true}', 4.8, 2800),
('Nintendo Switch OLED', 'Handheld console with vibrant OLED display', 349.99, 40, 6, 10, 'https://example.com/nintendoswitch.jpg', '{"storage": "64GB", "display": "7 inch OLED", "battery": "4.5-9 hours", "portable": true}', 4.7, 1500);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_rating ON products(rating);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_brands_updated_at BEFORE UPDATE ON brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
