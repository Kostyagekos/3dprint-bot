import sqlite3

conn = sqlite3.connect("settings.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS prices (
    tech TEXT PRIMARY KEY,
    price REAL
)
""")

# Значения по умолчанию
default_prices = {
    "FDM": 4.0,
    "SLA": 40.0,
    "SLS": 35.0,
    "Projet 2500W": 1000.0
}

for tech, price in default_prices.items():
    cur.execute("INSERT OR IGNORE INTO prices (tech, price) VALUES (?, ?)", (tech, price))

conn.commit()
conn.close()
