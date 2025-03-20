#!/venv/bin/python3
import sys
import argparse
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
from typing import List, Tuple, Dict
import time
import csv
import os
from collections import defaultdict

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)
Faker.seed(42)
fake = Faker()

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
def generate_users() -> List[Tuple]:
    """Generate 500 user records."""
    users = []
    cities = ['Dallas', 'Philadelphia', 'New York']
    roles = ['attendee'] * 80 + ['organizer'] * 15 + ['admin'] * 5
    random.shuffle(roles)
    for i in range(500):
        first_name = fake.first_name()
        last_name = fake.last_name()
        timestamp = int(time.time() * 1000) + i
        email = f"{first_name.lower()}.{last_name.lower()}.{timestamp}@example.com"
        password_hash = f"hash{i}"
        city = random.choice(cities)
        phone = generate_phone_number(city)
        role = roles[i % 100]
        created_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        updated_at = created_at
        users.append((first_name, last_name, email, password_hash, phone, role, created_at, updated_at))
    return users

def generate_venues() -> List[Tuple]:
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

def generate_events(organizer_ids: List[int], venue_ids: List[int]) -> List[Tuple]:
    """Generate 15 event records with future times."""
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

def generate_event_categories() -> List[Tuple]:
    """Generate 5 event category records."""
    return [
        ('Conference', 'Professional development and networking events'),
        ('Festival', 'Music, art, or cultural celebrations'),
        ('Exhibition', 'Showcases of art, products, or services'),
        ('Sports', 'Competitive or recreational sporting events'),
        ('Workshop', 'Hands-on learning sessions')
    ]

def generate_event_category_mapping(event_ids: List[int], category_ids: List[int]) -> List[Tuple]:
    """Generate event-category mappings (1-3 categories per event)."""
    mappings = []
    for event_id in event_ids:
        num_categories = random.randint(1, 3)
        selected = random.sample(category_ids, num_categories)
        for cat in selected:
            mappings.append((event_id, cat))
    return mappings

def generate_tickets(event_ids: List[int], event_capacities: Dict[int, int]) -> List[Tuple]:
    """Generate tickets respecting event capacity."""
    tickets = []
    for event_id in event_ids:
        capacity = event_capacities[event_id]
        ga_lower = min(300, capacity // 2)
        ga_upper = min(1000, capacity // 2)
        ga_quantity = random.randint(ga_lower, ga_upper)
        
        remaining_capacity = capacity - ga_quantity
        vip_lower = min(300, remaining_capacity)
        vip_upper = min(600, remaining_capacity)
        vip_quantity = random.randint(vip_lower, vip_upper)
        
        tickets.append((
            event_id, 'General Admission', round(random.uniform(20, 50), 2),
            ga_quantity, 0,
            fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S"),
            fake.future_datetime(end_date="+365d").strftime("%Y-%m-%d %H:%M:%S"),
            fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        ))
        tickets.append((
            event_id, 'VIP', round(random.uniform(50, 150), 2),
            vip_quantity, 0,
            fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S"),
            fake.future_datetime(end_date="+365d").strftime("%Y-%m-%d %H:%M:%S"),
            fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        ))
    return tickets

def generate_registrations(user_ids: List[int], event_ids: List[int], ticket_map: Dict[int, List[int]], 
                         ticket_prices: Dict[int, float], tickets_remaining: Dict[int, int], 
                         event_capacities: Dict[int, int], event_reg_totals: Dict[int, int]) -> List[Tuple]:
    """Generate registrations respecting ticket and event capacity."""
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
        remaining_capacity = event_capacities[event_id] - event_reg_totals.get(event_id, 0)
        if remaining_capacity <= 0:
            continue
        quantity = random.randint(1, min(5, available, remaining_capacity))
        price = ticket_prices[ticket_id]
        total_amount = round(quantity * price, 2)
        status = 'confirmed'
        registered_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        payment_status = 'paid' if random.random() < 0.4 else 'unpaid'
        registrations.append((user_id, event_id, ticket_id, quantity, total_amount, status, registered_at, payment_status))
        tickets_remaining[ticket_id] -= quantity
        event_reg_totals[event_id] = event_reg_totals.get(event_id, 0) + quantity
    return registrations

def generate_payments(registrations: List[Tuple]) -> List[Tuple]:
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

def generate_notifications(registrations: List[Tuple]) -> List[Tuple]:
    """Generate notifications based on registrations."""
    notifications = []
    types = ['email', 'sms', 'push']
    for reg in registrations:
        sent_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S") if reg[7] == 'paid' else None
        notifications.append((
            reg[0], reg[1], f"Your registration for event {reg[1]} is confirmed",
            random.choice(types), 'sent' if reg[7] == 'paid' else 'pending', sent_at
        ))
        if random.random() < 0.5:
            notifications.append((
                reg[0], reg[1], "Reminder: Your event starts soon!",
                random.choice(types), 'pending', None
            ))
    return notifications

def generate_speakers(num_speakers: int) -> List[Tuple]:
    """Generate speaker records with phone numbers limited to 12 characters."""
    speakers = []
    for i in range(num_speakers):
        first_name = fake.first_name()
        last_name = fake.last_name()
        bio = fake.paragraph(nb_sentences=3)
        email = f"{first_name.lower()}.{last_name.lower()}{i}@speaker.com"
        area_code = random.randint(100, 999)
        exchange_code = random.randint(100, 999)
        line_number = random.randint(1000, 9999)
        phone = f"{area_code}-{exchange_code}-{line_number}"
        created_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        speakers.append((first_name, last_name, bio, email, phone, created_at))
    return speakers

def generate_sponsors(num_sponsors: int) -> List[Tuple]:
    """Generate sponsor records."""
    sponsors = []
    for i in range(num_sponsors):
        name = fake.company()
        description = fake.catch_phrase()
        logo_url = f"https://example.com/logos/{i}.png"
        website = fake.url()
        created_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        sponsors.append((name, description, logo_url, website, created_at))
    return sponsors

def generate_sessions(event_ids: List[int], speaker_ids: List[int], 
                     num_sessions_per_event: Tuple[int, int], events: List[Tuple]) -> List[Tuple]:
    """Generate session records within event time frames."""
    sessions = []
    event_time_map = {event_id: (datetime.strptime(event[2], "%Y-%m-%d %H:%M:%S"),
                                datetime.strptime(event[3], "%Y-%m-%d %H:%M:%S"))
                     for event_id, event in enumerate(events, 1)}
    
    for event_id in event_ids:
        start_time, end_time = event_time_map[event_id]
        duration = (end_time - start_time).total_seconds() / 3600
        num_sessions = random.randint(num_sessions_per_event[0], num_sessions_per_event[1])
        for _ in range(num_sessions):
            speaker_id = random.choice(speaker_ids)
            title = fake.sentence(nb_words=4)
            description = fake.paragraph(nb_sentences=2)
            session_duration = random.uniform(0.5, min(4, duration))
            session_start = start_time + timedelta(hours=random.uniform(0, duration - session_duration))
            session_end = session_start + timedelta(hours=session_duration)
            room = f"Room {random.randint(1, 10)}"
            created_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
            sessions.append((
                event_id, speaker_id, title, description,
                session_start.strftime("%Y-%m-%d %H:%M:%S"),
                session_end.strftime("%Y-%m-%d %H:%M:%S"),
                room, created_at
            ))
    return sessions

def generate_event_sponsors(event_ids: List[int], sponsor_ids: List[int], 
                          max_sponsors_per_event: int) -> List[Tuple]:
    """Generate event-sponsor mappings."""
    event_sponsors = []
    sponsorship_levels = ['Gold', 'Silver', 'Bronze']
    for event_id in event_ids:
        num_sponsors = random.randint(0, max_sponsors_per_event)
        selected_sponsors = random.sample(sponsor_ids, min(num_sponsors, len(sponsor_ids)))
        for sponsor_id in selected_sponsors:
            level = random.choice(sponsorship_levels)
            contribution = round(random.uniform(1000, 10000), 2)
            event_sponsors.append((event_id, sponsor_id, level, contribution))
    return event_sponsors

def generate_feedback(registrations: List[Tuple], feedback_probability: float) -> List[Tuple]:
    """Generate feedback for paid registrations."""
    feedback = []
    for reg in registrations:
        if reg[7] == 'paid' and random.random() < feedback_probability:
            event_id = reg[1]
            user_id = reg[0]
            rating = random.randint(1, 5)
            comment = fake.sentence(nb_words=10)
            submitted_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
            feedback.append((event_id, user_id, rating, comment, submitted_at))
    return feedback

def generate_promotions(event_ids: List[int], max_promos_per_event: int) -> List[Tuple]:
    """Generate promotion records with unique codes."""
    promotions = []
    used_codes = set()
    for event_id in event_ids:
        num_promos = random.randint(0, max_promos_per_event)
        for _ in range(num_promos):
            code = fake.word().upper() + str(random.randint(100, 999))
            while code in used_codes:
                code = fake.word().upper() + str(random.randint(100, 999))
            used_codes.add(code)
            discount_percentage = round(random.uniform(5, 50), 2)
            valid_from = fake.future_datetime(end_date="+30d").strftime("%Y-%m-%d %H:%M:%S")
            valid_to = (datetime.strptime(valid_from, "%Y-%m-%d %H:%M:%S") + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            created_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
            promotions.append((event_id, code, discount_percentage, valid_from, valid_to, created_at))
    return promotions

def calculate_total_registrations(registrations: List[Tuple]) -> Dict[int, int]:
    """Calculate total quantity registered per event."""
    total_regs = defaultdict(int)
    for reg in registrations:
        event_id = reg[1]
        quantity = reg[3]
        total_regs[event_id] += quantity
    return total_regs

def generate_waitlists(user_ids: List[int], event_ids: List[int], total_regs: Dict[int, int], 
                      event_capacities: Dict[int, int], min_waitlist: int, max_waitlist: int) -> List[Tuple]:
    """Generate waitlist records for sold-out events."""
    waitlists = []
    statuses = ['waiting', 'notified', 'registered']
    for event_id in event_ids:
        if total_regs.get(event_id, 0) >= event_capacities[event_id]:
            num_waitlist = random.randint(min_waitlist, max_waitlist)
            selected_users = random.sample(user_ids, min(num_waitlist, len(user_ids)))
            for user_id in selected_users:
                joined_at = fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
                status = random.choice(statuses)
                waitlists.append((event_id, user_id, joined_at, status))
    return waitlists

def write_to_csv(filename: str, columns: List[str], data: List[Tuple]):
    """Export data to CSV only if file doesn't exist or forced."""
    if os.path.exists(filename) and not args.force:
        print(f"File {filename} already exists. Skipping.")
        return
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(data)
    print(f"Exported {len(data)} records to {filename}")

def generate_sql_insert(table: str, columns: List[str], data: List[Tuple]) -> str:
    """Generate SQL INSERT statements for a table, handling None as NULL."""
    values = ',\n'.join([
        f"({', '.join(['NULL' if value is None else repr(value) for value in row])})"
        for row in data
    ])
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n{values};\n\n"

def main():
    """Generate synthetic data and create SQL file for insertion."""
    parser = argparse.ArgumentParser(description='Generate synthetic event data')
    parser.add_argument('--force', action='store_true', 
                        help='Force regenerate all data and overwrite existing files')
    global args
    args = parser.parse_args()

    sql_content = []
    
    # Users
    users = generate_users()
    user_columns = ['first_name', 'last_name', 'email', 'password_hash', 'phone', 'role', 'created_at', 'updated_at']
    sql_content.append(generate_sql_insert('users', user_columns, users))

    # Venues
    venues = generate_venues()
    venue_columns = ['name', 'address', 'city', 'state', 'country', 'zip_code', 'latitude', 'longitude', 'capacity', 'created_at']
    sql_content.append(generate_sql_insert('venues', venue_columns, venues))

    # Event Categories
    event_categories = generate_event_categories()
    category_columns = ['name', 'description']
    sql_content.append(generate_sql_insert('event_categories', category_columns, event_categories))

    # Events
    organizer_ids = [i + 1 for i, u in enumerate(users) if u[5] in ('organizer', 'admin')]
    venue_ids = list(range(1, len(venues) + 1))
    events = generate_events(organizer_ids, venue_ids)
    event_columns = ['title', 'description', 'start_time', 'end_time', 'organizer_id', 'venue_id', 'capacity', 'status', 'created_at', 'updated_at']
    sql_content.append(generate_sql_insert('events', event_columns, events))
    event_ids = list(range(1, len(events) + 1))
    event_capacities = {i + 1: event[6] for i, event in enumerate(events)}

    # Tickets
    tickets = generate_tickets(event_ids, event_capacities)
    ticket_columns = ['event_id', 'ticket_type', 'price', 'quantity_available', 'quantity_sold', 'sales_start', 'sales_end', 'created_at']
    sql_content.append(generate_sql_insert('tickets', ticket_columns, tickets))

    # Event Category Mapping
    category_ids = list(range(1, len(event_categories) + 1))
    event_category_mappings = generate_event_category_mapping(event_ids, category_ids)
    mapping_columns = ['event_id', 'category_id']
    sql_content.append(generate_sql_insert('event_category_mapping', mapping_columns, event_category_mappings))

    # Registrations
    user_ids = list(range(1, len(users) + 1))
    ticket_map = {event_id: [ticket_id for ticket_id, t in enumerate(tickets, 1) if t[0] == event_id] for event_id in event_ids}
    ticket_prices = {ticket_id: t[2] for ticket_id, t in enumerate(tickets, 1)}
    tickets_remaining = {ticket_id: t[3] for ticket_id, t in enumerate(tickets, 1)}
    event_reg_totals = {}
    registrations = generate_registrations(user_ids, event_ids, ticket_map, ticket_prices, tickets_remaining, event_capacities, event_reg_totals)
    registration_columns = ['user_id', 'event_id', 'ticket_id', 'quantity', 'total_amount', 'status', 'registered_at', 'payment_status']
    sql_content.append(generate_sql_insert('registrations', registration_columns, registrations))

    # Update tickets' quantity_sold
    updated_tickets = []
    for ticket_id, t in enumerate(tickets, 1):
        orig_available = t[3]
        sold = orig_available - tickets_remaining.get(ticket_id, 0)
        sold = min(sold, orig_available)
        ticket_list = list(t)
        ticket_list[4] = sold
        updated_tickets.append(tuple(ticket_list))
    
    # Generate SQL for updated tickets
    sql_content.append(generate_sql_insert('tickets', ticket_columns, updated_tickets))

    # Payments
    payments = generate_payments(registrations)
    payment_columns = ['registration_id', 'user_id', 'amount', 'payment_method', 'transaction_id', 'payment_status', 'paid_at']
    sql_content.append(generate_sql_insert('payments', payment_columns, payments))

    # Notifications
    notifications = generate_notifications(registrations)
    notification_columns = ['user_id', 'event_id', 'message', 'type', 'status', 'sent_at']
    sql_content.append(generate_sql_insert('notifications', notification_columns, notifications))

    # Speakers
    num_speakers = 50
    speakers = generate_speakers(num_speakers)
    speakers_columns = ['first_name', 'last_name', 'bio', 'email', 'phone', 'created_at']
    sql_content.append(generate_sql_insert('speakers', speakers_columns, speakers))

    # Sponsors
    num_sponsors = 20
    sponsors = generate_sponsors(num_sponsors)
    sponsors_columns = ['name', 'description', 'logo_url', 'website', 'created_at']
    sql_content.append(generate_sql_insert('sponsors', sponsors_columns, sponsors))

    # Sessions
    speaker_ids = list(range(1, num_speakers + 1))
    sessions = generate_sessions(event_ids, speaker_ids, (1, 5), events)
    sessions_columns = ['event_id', 'speaker_id', 'title', 'description', 'start_time', 'end_time', 'room', 'created_at']
    sql_content.append(generate_sql_insert('sessions', sessions_columns, sessions))

    # Event Sponsors
    sponsor_ids = list(range(1, num_sponsors + 1))
    event_sponsors = generate_event_sponsors(event_ids, sponsor_ids, 3)
    event_sponsors_columns = ['event_id', 'sponsor_id', 'sponsorship_level', 'contribution_amount']
    sql_content.append(generate_sql_insert('event_sponsors', event_sponsors_columns, event_sponsors))

    # Feedback
    feedback = generate_feedback(registrations, 0.3)
    feedback_columns = ['event_id', 'user_id', 'rating', 'comment', 'submitted_at']
    sql_content.append(generate_sql_insert('feedback', feedback_columns, feedback))

    # Promotions
    promotions = generate_promotions(event_ids, 2)
    promotions_columns = ['event_id', 'code', 'discount_percentage', 'valid_from', 'valid_to', 'created_at']
    sql_content.append(generate_sql_insert('promotions', promotions_columns, promotions))

    # Waitlists
    total_regs = calculate_total_registrations(registrations)
    waitlists = generate_waitlists(user_ids, event_ids, total_regs, event_capacities, 10, 50)
    waitlists_columns = ['event_id', 'user_id', 'joined_at', 'status']
    sql_content.append(generate_sql_insert('waitlists', waitlists_columns, waitlists))

    # Write all SQL content to a file
    sql_filename = 'data_insert.sql'
    if os.path.exists(sql_filename) and not args.force:
        print(f"File {sql_filename} already exists. Skipping.")
        return
        
    with open(sql_filename, 'w') as f:
        f.write("-- Auto-generated SQL insert statements\n")
        f.write("-- Run this file to insert all generated data\n\n")
        f.write("SET time_zone = '+00:00';\n\n")  # Set session time zone to UTC
        f.write("BEGIN;\n\n")
        f.writelines(sql_content)
        f.write("COMMIT;\n")
    
    print(f"SQL file {sql_filename} created successfully!")

if __name__ == '__main__':
    if not sys.prefix.endswith('/venv'):
        print("❌ Please activate virtual environment first!")
        print("Run: source venv/bin/activate")
        sys.exit(1)
    main()