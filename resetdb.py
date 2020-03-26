import os
import sqlite3

# Remove the old database
if os.path.exists("claptrap.db"):
    os.remove("claptrap.db")

conn = sqlite3.connect('claptrap.db')
print("Connected!")

print("Creating table(s)...")
conn.execute('''CREATE TABLE greeting
         (ID INTEGER PRIMARY KEY AUTOINCREMENT,
         channel           TEXT    NOT NULL UNIQUE,
         greeting          TEXT     NOT NULL);''')

print("Creating indexes...")
conn.execute('''CREATE INDEX idx_greeting_channel ON greeting (channel);''')


conn.close()