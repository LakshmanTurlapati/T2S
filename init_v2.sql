-- Drop the existing event_management database if it exists
DROP DATABASE IF EXISTS event_management;

-- Create the event_management database
CREATE DATABASE event_management;

USE event_management;

-- Create tables with lowercase names

-- Users Table
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

-- Venues Table
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

-- Events Table
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
    created_at TIMESTAMP
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

-- Speakers Table (New)
CREATE TABLE speakers (
    speaker_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    bio TEXT,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    created_at TIMESTAMP
);

-- Sponsors Table (New)
CREATE TABLE sponsors (
    sponsor_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    logo_url VARCHAR(255),
    website VARCHAR(255),
    created_at TIMESTAMP
);

-- Sessions Table (New)
CREATE TABLE sessions (
    session_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(event_id),
    speaker_id INT REFERENCES speakers(speaker_id),
    title VARCHAR(100),
    description TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    room VARCHAR(50),
    created_at TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (speaker_id) REFERENCES speakers(speaker_id)
);

-- Event_Sponsors Table (New, junction table)
CREATE TABLE event_sponsors (
    event_id INT REFERENCES events(event_id),
    sponsor_id INT REFERENCES sponsors(sponsor_id),
    sponsorship_level VARCHAR(50),
    contribution_amount DECIMAL(10,2),
    PRIMARY KEY (event_id, sponsor_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id)
);

-- Feedback Table (New)
CREATE TABLE feedback (
    feedback_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(event_id),
    user_id INT REFERENCES users(user_id),
    rating INT,
    comment TEXT,
    submitted_at TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Promotions Table (New)
CREATE TABLE promotions (
    promotion_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(event_id),
    code VARCHAR(50) UNIQUE,
    discount_percentage DECIMAL(5,2),
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

-- Waitlists Table (New)
CREATE TABLE waitlists (
    waitlist_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(event_id),
    user_id INT REFERENCES users(user_id),
    joined_at TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('waiting', 'notified', 'registered')) DEFAULT 'waiting',
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);