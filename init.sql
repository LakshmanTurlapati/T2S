-- Create database (will be auto-created by PostgreSQL)
\connect postgres
DROP DATABASE IF EXISTS event_management;
CREATE DATABASE event_management;
\connect event_management

-- Create tables with lowercase names
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    phone VARCHAR(15),
    role VARCHAR(20) CHECK (role IN ('attendee', 'organizer', 'admin')) DEFAULT 'attendee',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE venues (
    venue_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    zip_code VARCHAR(10),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    capacity INT,
    created_at TIMESTAMP
);

CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    title VARCHAR(100),
    description TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    organizer_id INT REFERENCES users(user_id),
    venue_id INT REFERENCES venues(venue_id),
    capacity INT,
    status VARCHAR(20) CHECK (status IN ('draft', 'published', 'canceled', 'completed')) DEFAULT 'draft',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Tickets Table
CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(event_id),
    ticket_type VARCHAR(50),
    price DECIMAL(10,2),
    quantity_available INT,
    quantity_sold INT DEFAULT 0,
    sales_start TIMESTAMP,
    sales_end TIMESTAMP,
    created_at TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

-- Registrations Table
CREATE TABLE registrations (
    registration_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    event_id INT REFERENCES events(event_id),
    ticket_id INT REFERENCES tickets(ticket_id),
    quantity INT,
    total_amount DECIMAL(10,2),
    status VARCHAR(20) CHECK (status IN ('pending', 'confirmed', 'canceled')) DEFAULT 'pending',
    registered_at TIMESTAMP,
    payment_status VARCHAR(20) CHECK (payment_status IN ('unpaid', 'paid', 'refunded')) DEFAULT 'unpaid',
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);

-- Event_Categories Table
CREATE TABLE event_categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    description TEXT
);

-- Event_Category_Mapping Table (junction table)
CREATE TABLE event_category_mapping (
    event_id INT REFERENCES events(event_id),
    category_id INT REFERENCES event_categories(category_id),
    PRIMARY KEY (event_id, category_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (category_id) REFERENCES event_categories(category_id)
);

-- Payments Table
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    registration_id INT REFERENCES registrations(registration_id),
    user_id INT REFERENCES users(user_id),
    amount DECIMAL(10,2),
    payment_method VARCHAR(20) CHECK (payment_method IN ('credit_card', 'paypal', 'bank_transfer', 'cash')),
    transaction_id VARCHAR(100),
    payment_status VARCHAR(20) CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')) DEFAULT 'pending',
    paid_at TIMESTAMP,
    FOREIGN KEY (registration_id) REFERENCES registrations(registration_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Notifications Table
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    event_id INT REFERENCES events(event_id),
    message TEXT,
    type VARCHAR(20) CHECK (type IN ('email', 'sms', 'push')) DEFAULT 'email',
    status VARCHAR(20) CHECK (status IN ('pending', 'sent', 'failed')) DEFAULT 'pending',
    sent_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

-- 2. Populate Tables with Synthetic Data

-- -- Venues (10 records)
-- INSERT INTO venues (name, address, city, state, country, zip_code, latitude, longitude, capacity, created_at) VALUES
-- ('Dallas Convention Center', '650 S Griffin St', 'Dallas', 'TX', 'USA', '75202', 32.7767, -96.7970, 10000, NOW()),
-- ('AT&T Stadium', '1 AT&T Way', 'Arlington', 'TX', 'USA', '76011', 32.7473, -97.0945, 80000, NOW()),
-- ('Texas Theatre', '231 W Jefferson Blvd', 'Dallas', 'TX', 'USA', '75208', 32.7431, -96.8286, 500, NOW()),
-- ('Philadelphia Convention Center', '1101 Arch St', 'Philadelphia', 'PA', 'USA', '19107', 39.9526, -75.1652, 20000, NOW()),
-- ('Lincoln Financial Field', '1020 Pattison Ave', 'Philadelphia', 'PA', 'USA', '19148', 39.9008, -75.1684, 70000, NOW()),
-- ('The Fillmore Philadelphia', '29 E Allen St', 'Philadelphia', 'PA', 'USA', '19123', 39.9662, -75.1337, 3000, NOW()),
-- ('Madison Square Garden', '4 Pennsylvania Plaza', 'New York', 'NY', 'USA', '10001', 40.7505, -73.9934, 20000, NOW()),
-- ('Barclays Center', '620 Atlantic Ave', 'Brooklyn', 'NY', 'USA', '11217', 40.6827, -73.9754, 19000, NOW()),
-- ('Apollo Theater', '253 W 125th St', 'New York', 'NY', 'USA', '10027', 40.8099, -73.9509, 1500, NOW()),
-- ('Central Park SummerStage', 'Rumsey Playfield', 'New York', 'NY', 'USA', '10021', 40.7712, -73.9675, 5000, NOW());

-- -- Users (500 total, sample of 5 shown)
-- INSERT INTO users (first_name, last_name, email, password_hash, phone, role, created_at, updated_at) VALUES
-- ('John', 'Doe', 'john.doe@example.com', 'hash1234', '2145551234', 'organizer', NOW(), NOW()),
-- ('Jane', 'Smith', 'jane.smith@example.com', 'hash5678', '2675555678', 'admin', NOW(), NOW()),
-- ('Alice', 'Johnson', 'alice.j@example.com', 'hash9012', '6465559012', 'attendee', NOW(), NOW()),
-- ('Bob', 'Williams', 'bob.w@example.com', 'hash3456', '4695553456', 'organizer', NOW(), NOW()),
-- ('Emma', 'Davis', 'emma.d@example.com', 'hash7890', '2155557890', 'attendee', NOW(), NOW());
-- -- Note: Generate 495 more users with a script (e.g., Python with faker) for names, emails, phones across Dallas (area code 214/469), Philadelphia (215/267), NYC (646/212).

-- -- Event_Categories (5 records)
-- INSERT INTO event_categories (name, description) VALUES
-- ('Conference', 'Professional development and networking events'),
-- ('Festival', 'Music, art, or cultural celebrations'),
-- ('Exhibition', 'Showcases of art, products, or services'),
-- ('Sports', 'Competitive or recreational sporting events'),
-- ('Workshop', 'Hands-on learning sessions');

-- -- Events (15 records)
-- INSERT INTO events (title, description, start_time, end_time, organizer_id, venue_id, capacity, status, created_at, updated_at) VALUES
-- ('Dallas Tech Conference', 'Latest in tech innovation', '2025-03-01 09:00:00', '2025-03-01 17:00:00', 1, 1, 500, 'published', NOW(), NOW()),
-- ('Texas Music Fest', 'Live country music', '2025-04-10 14:00:00', '2025-04-10 23:00:00', 4, 2, 2000, 'published', NOW(), NOW()),
-- ('Dallas Art Show', 'Local artists exhibit', '2025-05-15 10:00:00', '2025-05-15 18:00:00', 1, 3, 300, 'published', NOW(), NOW()),
-- ('Philly Food Festival', 'Taste of Philadelphia', '2025-06-20 12:00:00', '2025-06-20 20:00:00', 4, 4, 1000, 'published', NOW(), NOW()),
-- ('Eagles Fan Day', 'Meet the players', '2025-07-01 13:00:00', '2025-07-01 16:00:00', 1, 5, 5000, 'published', NOW(), NOW()),
-- ('Philly Jazz Night', 'Smooth jazz performances', '2025-08-15 19:00:00', '2025-08-15 23:00:00', 4, 6, 800, 'published', NOW(), NOW()),
-- ('NYC Fashion Expo', 'Latest fashion trends', '2025-09-10 10:00:00', '2025-09-10 18:00:00', 1, 7, 1000, 'published', NOW(), NOW()),
-- ('Brooklyn Beer Fest', 'Craft beer tasting', '2025-10-05 15:00:00', '2025-10-05 21:00:00', 4, 8, 1500, 'published', NOW(), NOW()),
-- ('Harlem Poetry Slam', 'Spoken word event', '2025-11-20 18:00:00', '2025-11-20 22:00:00', 1, 9, 400, 'published', NOW(), NOW()),
-- ('Central Park Yoga', 'Outdoor yoga session', '2025-12-01 08:00:00', '2025-12-01 10:00:00', 4, 10, 200, 'published', NOW(), NOW()),
-- ('Dallas Startup Pitch', 'Entrepreneur pitches', '2025-03-15 09:00:00', '2025-03-15 13:00:00', 1, 1, 200, 'published', NOW(), NOW()),
-- ('Philly Tech Workshop', 'Coding bootcamp', '2025-04-25 09:00:00', '2025-04-25 17:00:00', 4, 4, 150, 'published', NOW(), NOW()),
-- ('NYC Marathon Expo', 'Pre-race showcase', '2025-11-01 10:00:00', '2025-11-01 16:00:00', 1, 7, 3000, 'published', NOW(), NOW()),
-- ('Texas BBQ Cookoff', 'BBQ competition', '2025-06-10 11:00:00', '2025-06-10 18:00:00', 4, 2, 1000, 'published', NOW(), NOW()),
-- ('Philly Art Fair', 'Outdoor art market', '2025-07-15 10:00:00', '2025-07-15 17:00:00', 1, 6, 600, 'published', NOW(), NOW());

-- -- Tickets (30 records, 2 per event)
-- INSERT INTO tickets (event_id, ticket_type, price, quantity_available, quantity_sold, sales_start, sales_end, created_at) VALUES
-- (1, 'General Admission', 50.00, 400, 0, '2025-01-01 00:00:00', '2025-02-28 23:59:59', NOW()),
-- (1, 'VIP', 100.00, 100, 0, '2025-01-01 00:00:00', '2025-02-28 23:59:59', NOW()),
-- (2, 'General Admission', 30.00, 1500, 0, '2025-02-01 00:00:00', '2025-04-09 23:59:59', NOW()),
-- (2, 'VIP', 75.00, 500, 0, '2025-02-01 00:00:00', '2025-04-09 23:59:59', NOW()),
-- (3, 'General Admission', 15.00, 250, 0, '2025-03-01 00:00:00', '2025-05-14 23:59:59', NOW()),
-- (3, 'VIP', 40.00, 50, 0, '2025-03-01 00:00:00', '2025-05-14 23:59:59', NOW()),
-- (4, 'General Admission', 25.00, 800, 0, '2025-04-01 00:00:00', '2025-06-19 23:59:59', NOW()),
-- (4, 'VIP', 60.00, 200, 0, '2025-04-01 00:00:00', '2025-06-19 23:59:59', NOW()),
-- (5, 'General Admission', 20.00, 4000, 0, '2025-05-01 00:00:00', '2025-06-30 23:59:59', NOW()),
-- (5, 'VIP', 50.00, 1000, 0, '2025-05-01 00:00:00', '2025-06-30 23:59:59', NOW()),
-- (6, 'General Admission', 35.00, 600, 0, '2025-06-01 00:00:00', '2025-08-14 23:59:59', NOW()),
-- (6, 'VIP', 80.00, 200, 0, '2025-06-01 00:00:00', '2025-08-14 23:59:59', NOW()),
-- (7, 'General Admission', 60.00, 800, 0, '2025-07-01 00:00:00', '2025-09-09 23:59:59', NOW()),
-- (7, 'VIP', 120.00, 200, 0, '2025-07-01 00:00:00', '2025-09-09 23:59:59', NOW()),
-- (8, 'General Admission', 25.00, 1200, 0, '2025-08-01 00:00:00', '2025-10-04 23:59:59', NOW()),
-- (8, 'VIP', 55.00, 300, 0, '2025-08-01 00:00:00', '2025-10-04 23:59:59', NOW()),
-- (9, 'General Admission', 10.00, 350, 0, '2025-09-01 00:00:00', '2025-11-19 23:59:59', NOW()),
-- (9, 'VIP', 30.00, 50, 0, '2025-09-01 00:00:00', '2025-11-19 23:59:59', NOW()),
-- (10, 'General Admission', 0.00, 200, 0, '2025-10-01 00:00:00', '2025-11-30 23:59:59', NOW()),
-- (10, 'Donation', 10.00, 100, 0, '2025-10-01 00:00:00', '2025-11-30 23:59:59', NOW()),
-- (11, 'General Admission', 40.00, 150, 0, '2025-01-15 00:00:00', '2025-03-14 23:59:59', NOW()),
-- (11, 'VIP', 80.00, 50, 0, '2025-01-15 00:00:00', '2025-03-14 23:59:59', NOW()),
-- (12, 'General Admission', 45.00, 120, 0, '2025-02-15 00:00:00', '2025-04-24 23:59:59', NOW()),
-- (12, 'VIP', 90.00, 30, 0, '2025-02-15 00:00:00', '2025-04-24 23:59:59', NOW()),
-- (13, 'General Admission', 30.00, 2500, 0, '2025-09-01 00:00:00', '2025-10-31 23:59:59', NOW()),
-- (13, 'VIP', 70.00, 500, 0, '2025-09-01 00:00:00', '2025-10-31 23:59:59', NOW()),
-- (14, 'General Admission', 20.00, 800, 0, '2025-04-01 00:00:00', '2025-06-09 23:59:59', NOW()),
-- (14, 'VIP', 50.00, 200, 0, '2025-04-01 00:00:00', '2025-06-09 23:59:59', NOW()),
-- (15, 'General Admission', 15.00, 500, 0, '2025-05-15 00:00:00', '2025-07-14 23:59:59', NOW()),
-- (15, 'VIP', 35.00, 100, 0, '2025-05-15 00:00:00', '2025-07-14 23:59:59', NOW());

-- -- Registrations (2500 total, sample of 5 shown)
-- INSERT INTO registrations (user_id, event_id, ticket_id, quantity, total_amount, status, registered_at, payment_status) VALUES
-- (3, 1, 1, 2, 100.00, 'confirmed', NOW(), 'paid'),
-- (5, 2, 3, 1, 30.00, 'confirmed', NOW(), 'paid'),
-- (3, 4, 7, 3, 75.00, 'confirmed', NOW(), 'paid'),
-- (5, 7, 13, 1, 60.00, 'pending', NOW(), 'unpaid'),
-- (3, 10, 19, 1, 0.00, 'confirmed', NOW(), 'paid');
-- -- Note: Generate 2495 more registrations, assuming each of 500 users registers for ~5 events on average. Randomly assign user_id (1-500), event_id (1-15), ticket_id (matching event), and adjust quantity/total_amount.

-- -- Payments (1000-3000 total, sample of 5 shown, tied to paid registrations)
-- INSERT INTO payments (registration_id, user_id, amount, payment_method, transaction_id, payment_status, paid_at) VALUES
-- (1, 3, 100.00, 'credit_card', 'txn_001', 'completed', NOW()),
-- (2, 5, 30.00, 'paypal', 'txn_002', 'completed', NOW()),
-- (3, 3, 75.00, 'credit_card', 'txn_003', 'completed', NOW()),
-- (4, 5, 60.00, 'bank_transfer', 'txn_004', 'pending', NOW()),
-- (5, 3, 0.00, 'cash', 'txn_005', 'completed', NOW());
-- -- Note: Generate 1000-3000 payments, assuming 50% of 2500 registrations are paid (1250 avg.). Match registration_id and user_id from registrations where payment_status = 'paid'.

-- -- Event_Category_Mapping (15 records, one per event)
-- INSERT INTO event_category_mapping (event_id, category_id) VALUES
-- (1, 1), -- Conference
-- (2, 2), -- Festival
-- (3, 3), -- Exhibition
-- (4, 2), -- Festival
-- (5, 4), -- Sports
-- (6, 2), -- Festival
-- (7, 3), -- Exhibition
-- (8, 2), -- Festival
-- (9, 3), -- Exhibition
-- (10, 5), -- Workshop
-- (11, 1), -- Conference
-- (12, 5), -- Workshop
-- (13, 3), -- Exhibition
-- (14, 2), -- Festival
-- (15, 3); -- Exhibition

-- -- Notifications (sample of 5 shown, scale to hundreds/thousands)
-- INSERT INTO notifications (user_id, event_id, message, type, status, sent_at) VALUES
-- (3, 1, 'Your registration for Dallas Tech Conference is confirmed!', 'email', 'sent', NOW()),
-- (5, 2, 'Texas Music Fest is tomorrow!', 'sms', 'pending', NOW()),
-- (3, 4, 'Payment received for Philly Food Festival', 'email', 'sent', NOW()),
-- (5, 7, 'Reminder: NYC Fashion Expo in 2 days', 'push', 'sent', NOW()),
-- (3, 10, 'See you at Central Park Yoga!', 'email', 'sent', NOW());
-- -- Note: Generate notifications for registrations, reminders, etc., tied to user_id and event_id.