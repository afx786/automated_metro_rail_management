import sqlite3
import random

# Create the database file
conn = sqlite3.connect('kmrl_real_maximo.db')
cursor = conn.cursor()

# Create tables
cursor.executescript('''
CREATE TABLE trainsets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    fitness_valid BOOLEAN,
    job_card_open BOOLEAN,
    branding TEXT,
    mileage REAL,
    needs_deep_clean BOOLEAN
);

CREATE TABLE plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME,
    params TEXT
);

CREATE TABLE plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER,
    trainset_code TEXT,
    status TEXT,
    reason TEXT,
    brand TEXT,
    mileage REAL,
    needs_deep_clean BOOLEAN,
    FOREIGN KEY (plan_id) REFERENCES plans (id)
);
''')

# Generate random data for 25 trains
brands = ['Alstom', 'Siemens', 'Bombardier', 'Hyundai Rotem', 'CRRC', None]

for i in range(1, 26):
    code = f"KM{str(i).zfill(2)}"
    fitness_valid = random.choice([0, 1])
    job_card_open = random.choice([0, 1])
    branding = random.choice(brands)
    mileage = round(random.uniform(500, 5000), 1)
    needs_deep_clean = random.choice([0, 1])
    
    cursor.execute('''
    INSERT INTO trainsets (code, fitness_valid, job_card_open, branding, mileage, needs_deep_clean)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (code, fitness_valid, job_card_open, branding, mileage, needs_deep_clean))

conn.commit()
conn.close()

print("✅ kmrl_real_maximo.db file created successfully!")