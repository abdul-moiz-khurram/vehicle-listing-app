-- =====================================================
-- FILE: sql/schema.sql
-- PURPOSE: Database schema for Vehicle Listing Platform
-- =====================================================

-- =========================
-- TABLE: users
-- =========================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    email VARCHAR(120) UNIQUE NOT NULL,

    password VARCHAR(200) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- TABLE: brands
-- =========================
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- =========================
-- TABLE: vehicles
-- =========================
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    price NUMERIC NOT NULL,
    model_year INT NOT NULL,
    description TEXT,

    brand_id INT NOT NULL,
    user_id INT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    is_deleted BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_brand
        FOREIGN KEY (brand_id)
        REFERENCES brands(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- =========================
-- TABLE: vehicle_images
-- =========================
CREATE TABLE vehicle_images (
    id SERIAL PRIMARY KEY,
    vehicle_id INT NOT NULL,
    image_path TEXT NOT NULL,

    CONSTRAINT fk_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(id)
        ON DELETE CASCADE
);