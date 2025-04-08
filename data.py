#!/venv/bin/python3
import sys 
import argparse
import psycopg2.extras
import psycopg2
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
from typing import List, Tuple
import time
import csv
import os
from collections import defaultdict

fake = Faker()
random.seed(42)
np.random.seed(42)

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'event_management',
    'user': 'event_admin',
    'password': 'securepass'
}

# Helper function
def generate_phone_number(city: str) -> str:
    """Generate realistic phone numbers with city-specific area codes."""
    area_codes = {
        'Dallas': ['214', '469', '972'],
        'Philadelphia': ['215', '267', '445'],
        'New York': ['212', '646', '718', '917']
    }
    area_code = random.choice(area_codes.get(city, ['800']))
    return f"{area_code}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"

# Data generation functions
def generate_users() -> list:
    """Generate 500 user records."""
    users = []
    cities = ['Dallas', 'Philadelphia', 'New York']
    roles = ['attendee'] * 80 + ['organizer'] * 15 + ['admin'] * 5
    random.shuffle(roles)
    for i in range(500):
        first_name = fake.first_name()
        last_name = fake.last_name()
        timestamp = int(time.time() * 1000) + i  # Ensure uniqueness in email
        email = f"{first_name.lower()}.{last_name.lower()}.{timestamp}@example.com"
        password_hash = f"hash{i}"
        city = random.choice(cities)
        phone = generate_phone_number(city)
        role = roles[i % 100]
        created_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        updated_at = created_at
        users.append((first_name, last_name, email, password_hash, phone, role, created_at, updated_at))
    return users

def generate_venues() -> list:
    """Generate 10 venue records with realistic data."""
    venues = []
    cities = ['Dallas', 'Philadelphia', 'New York']
    for _ in range(10):
        city = random.choice(cities)
        name = f"{city} {fake.company()} Center"
        address = fake.street_address()
        state = 'TX' if city == 'Dallas' else ('PA' if city == 'Philadelphia' else 'NY')
        country = 'USA'
        zip_code = fake.zipcode()
        latitude = float(fake.latitude())
        longitude = float(fake.longitude())
        capacity = random.randint(500, 10000)
        created_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        venues.append((name, address, city, state, country, zip_code, latitude, longitude, capacity, created_at))
    return venues

def generate_events(organizer_ids: list, venue_ids: list) -> list:
    """Generate 15 event records with times in the future and realistic details."""
    events = []
    for _ in range(15):
        title = fake.sentence(nb_words=4)
        description = fake.text(max_nb_chars=200)
        start_time = fake.future_datetime(end_date="+365d")
        end_time = start_time + timedelta(hours=random.randint(2, 8))
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        organizer_id = random.choice(organizer_ids)
        venue_id = random.choice(venue_ids)
        capacity = random.randint(100, 5000)
        status = random.choice(['draft', 'published', 'canceled', 'completed'])
        created_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        updated_at = created_at
        events.append((title, description, start_time_str, end_time_str, organizer_id, venue_id, capacity, status, created_at, updated_at))
    return events

def generate_event_categories() -> list:
    """Generate 5 event category records."""
    return [
        ('Conference', 'Professional development and networking events'),
        ('Festival', 'Music, art, or cultural celebrations'),
        ('Exhibition', 'Showcases of art, products, or services'),
        ('Sports', 'Competitive or recreational sporting events'),
        ('Workshop', 'Hands-on learning sessions')
    ]

def generate_event_category_mapping(event_ids: list, category_ids: list) -> list:
    """Generate event-category mappings assigning each event 1 to 3 categories."""
    mappings = []
    for event_id in event_ids:
        num_categories = random.randint(1, 3)
        selected = random.sample(category_ids, num_categories)
        for cat in selected:
            mappings.append((event_id, cat))
    return mappings

def generate_notifications(registrations: list) -> list:
    """Generate notifications based on registrations."""
    notifications = []
    types = ['email', 'sms', 'push']
    for reg in registrations:
        notifications.append((
            reg[0],  # user_id
            reg[1],  # event_id
            f"Your registration for event {reg[1]} is confirmed",
            random.choice(types),
            'sent' if reg[7] == 'paid' else 'pending',
            fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        ))
        if random.random() < 0.5:
            notifications.append((
                reg[0],
                reg[1],
                "Reminder: Your event starts soon!",
                random.choice(types),
                'pending',
                None
            ))
    return notifications

def generate_registrations(user_ids: list, event_ids: list, ticket_map: dict, ticket_prices: dict, tickets_remaining: dict) -> list:
    """Generate registration records while respecting ticket capacity."""
    registrations = []
    desired_count = 2500
    attempts = 0
    while len(registrations) < desired_count and attempts < desired_count * 10:
        attempts += 1
        user_id = random.choice(user_ids)
        event_id = random.choice(event_ids)
        possible_tickets = ticket_map.get(event_id, [])
        if not possible_tickets:
            continue
        ticket_id = random.choice(possible_tickets)
        available = tickets_remaining.get(ticket_id, 0)
        if available <= 0:
            continue
        quantity = random.randint(1, 5)
        if quantity > available:
            quantity = available
        price = ticket_prices[ticket_id]
        total_amount = round(quantity * price, 2)
        status = 'confirmed'
        registered_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        payment_status = 'paid' if random.random() < 0.4 else 'unpaid'
        registrations.append((user_id, event_id, ticket_id, quantity, total_amount, status, registered_at, payment_status))
        tickets_remaining[ticket_id] -= quantity
    return registrations

def generate_payments(registrations: list) -> list:
    """Generate payment records for up to 1000 paid registrations."""
    payments = []
    payment_methods = ['credit_card', 'paypal', 'bank_transfer', 'cash']
    paid_regs = [(i, reg) for i, reg in enumerate(registrations) if reg[7] == 'paid']
    for idx, reg in paid_regs[:1000]:
        registration_id = idx + 1
        user_id = reg[0]
        amount = reg[4]
        payment_method = random.choice(payment_methods)
        transaction_id = f"txn_{fake.uuid4()}"
        payment_status = 'completed'
        paid_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        payments.append((registration_id, user_id, amount, payment_method, transaction_id, payment_status, paid_at))
    return payments

# Database operations
def create_connection():
    """Create a database connection with retry logic."""
    attempts = 0
    max_attempts = 5
    while attempts < max_attempts:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print("Connected to database successfully!")
            return conn
        except psycopg2.OperationalError as e:
            attempts += 1
            print(f"Connection attempt {attempts}/{max_attempts} failed: {e}")
            time.sleep(5)
    raise Exception("Failed to connect to database after multiple attempts")

def batch_insert(conn, table: str, columns: List[str], data: List[Tuple], args) -> None:
    """Insert data only if table is empty or forced"""
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count > 0 and not args.force:
            print(f"Table {table} already has {count} records. Skipping insertion.")
            return
    placeholders = ', '.join(['%s'] * len(columns))
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    with conn.cursor() as cursor:
        psycopg2.extras.execute_batch(cursor, query, data)
    conn.commit()
    print(f"Inserted {len(data)} records into {table}")

def write_to_csv(filename: str, columns: list, data: list, args) -> None:
    """Export data to CSV only if file doesn't exist or forced"""
    if os.path.exists(filename) and not args.force:
        print(f"File {filename} already exists. Skipping.")
        return
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(data)
    print(f"Exported {len(data)} records to {filename}")

def main():
    """Generate all synthetic data, insert into the database, and export to CSV files."""
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Generate synthetic event data')
    parser.add_argument('--force', action='store_true', 
                      help='Force regenerate all data and overwrite existing files')
    args = parser.parse_args()
    
    conn = create_connection()
    try:
        # Check if data already exists
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count > 0 and not args.force:
                print("Data already exists. Use --force to regenerate.")
                return

        # Users
        users = generate_users()
        user_columns = ['first_name', 'last_name', 'email', 'password_hash', 'phone', 'role', 'created_at', 'updated_at']
        batch_insert(conn, 'users', user_columns, users, args)
        write_to_csv('csv/users.csv', user_columns, users, args)

        # Venues
        venues = generate_venues()
        venue_columns = ['name', 'address', 'city', 'state', 'country', 'zip_code', 'latitude', 'longitude', 'capacity', 'created_at']
        batch_insert(conn, 'venues', venue_columns, venues, args)
        write_to_csv('csv/venues.csv', venue_columns, venues, args)

        # Event Categories
        event_categories = generate_event_categories()
        category_columns = ['name', 'description']
        batch_insert(conn, 'event_categories', category_columns, event_categories, args)
        write_to_csv('csv/event_categories.csv', category_columns, event_categories, args)

        # Events
        organizer_ids = [i + 1 for i, u in enumerate(users) if u[5] in ('organizer', 'admin')]
        venue_ids = list(range(1, len(venues) + 1))
        events = generate_events(organizer_ids, venue_ids)
        event_columns = ['title', 'description', 'start_time', 'end_time', 'organizer_id', 'venue_id', 'capacity', 'status', 'created_at', 'updated_at']
        batch_insert(conn, 'events', event_columns, events, args)
        write_to_csv('csv/events.csv', event_columns, events, args)

        # Tickets
        tickets = []
        for event_id in range(1, len(events) + 1):
            tickets.append((
                event_id,
                'General Admission',
                round(random.uniform(20, 50), 2),
                random.randint(300, 1000),
                0,
                fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S"),
                fake.future_datetime(end_date="+365d").strftime("%Y-%m-%d %H:%M:%S"),
                fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
            ))
            tickets.append((
                event_id,
                'VIP',
                round(random.uniform(50, 150), 2),
                random.randint(300, 600),
                0,
                fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S"),
                fake.future_datetime(end_date="+365d").strftime("%Y-%m-%d %H:%M:%S"),
                fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
            ))
        ticket_columns = ['event_id', 'ticket_type', 'price', 'quantity_available', 'quantity_sold', 'sales_start', 'sales_end', 'created_at']
        batch_insert(conn, 'tickets', ticket_columns, tickets, args)
        write_to_csv('csv/tickets.csv', ticket_columns, tickets, args)

        # Event Category Mapping
        event_ids = list(range(1, len(events) + 1))
        category_ids = list(range(1, len(event_categories) + 1))
        event_category_mappings = generate_event_category_mapping(event_ids, category_ids)
        mapping_columns = ['event_id', 'category_id']
        batch_insert(conn, 'event_category_mapping', mapping_columns, event_category_mappings, args)
        write_to_csv('csv/event_category_mapping.csv', mapping_columns, event_category_mappings, args)

        # Registrations
        user_ids = list(range(1, len(users) + 1))
        event_ids = list(range(1, len(events) + 1))
        ticket_map = {event_id: [ticket_id for ticket_id, t in enumerate(tickets, 1) if t[0] == event_id] for event_id in event_ids}
        ticket_prices = {ticket_id: t[2] for ticket_id, t in enumerate(tickets, 1)}
        tickets_remaining = {ticket_id: t[3] for ticket_id, t in enumerate(tickets, 1)}
        registrations = generate_registrations(user_ids, event_ids, ticket_map, ticket_prices, tickets_remaining)
        registration_columns = ['user_id', 'event_id', 'ticket_id', 'quantity', 'total_amount', 'status', 'registered_at', 'payment_status']
        batch_insert(conn, 'registrations', registration_columns, registrations, args)
        write_to_csv('csv/registrations.csv', registration_columns, registrations, args)

        # Update tickets' quantity_sold
        updated_tickets = []
        for ticket_id, t in enumerate(tickets, 1):
            orig_available = t[3]
            sold = orig_available - tickets_remaining.get(ticket_id, 0)
            sold = min(sold, orig_available)
            ticket_list = list(t)
            ticket_list[4] = sold
            updated_tickets.append(tuple(ticket_list))
        with conn.cursor() as cursor:
            for ticket_id, t in enumerate(updated_tickets, 1):
                cursor.execute("UPDATE tickets SET quantity_sold = %s WHERE ticket_id = %s", (t[4], ticket_id))
        conn.commit()
        write_to_csv('csv/tickets.csv', ticket_columns, updated_tickets, args)

        # Payments
        payments = generate_payments(registrations)
        payment_columns = ['registration_id', 'user_id', 'amount', 'payment_method', 'transaction_id', 'payment_status', 'paid_at']
        batch_insert(conn, 'payments', payment_columns, payments, args)
        write_to_csv('csv/payments.csv', payment_columns, payments, args)

        # Notifications
        notifications = generate_notifications(registrations)
        notification_columns = ['user_id', 'event_id', 'message', 'type', 'status', 'sent_at']
        batch_insert(conn, 'notifications', notification_columns, notifications, args)
        write_to_csv('csv/notifications.csv', notification_columns, notifications, args)

    finally:
        conn.close()

if __name__ == '__main__':
    # Verify we're using virtual environment Python
    if not sys.prefix.endswith('/venv'):
        print("❌ Please activate virtual environment first!")
        print("Run: source venv/bin/activate")
        sys.exit(1)
    main()