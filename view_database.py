import sqlite3

from core.db import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print('\n' + '='*60)
print('SMART CAMPUS SYSTEM - DATABASE CONTENTS')
print('='*60)

# Tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print(f'\nTables: {[t[0] for t in tables]}')

# Roles
print('\n--- ROLES ---')
cursor.execute('SELECT * FROM roles;')
for row in cursor.fetchall():
    print(row)

# Users
print('\n--- USERS ---')
cursor.execute('SELECT id, name, role_id, enrollment, username FROM users;')
for row in cursor.fetchall():
    print(row)

# Lectures
print('\n--- LECTURES ---')
cursor.execute('SELECT session_id, subject, room, start_time FROM lectures;')
for row in cursor.fetchall():
    print(row)

# Attendance
print('\n--- ATTENDANCE ---')
cursor.execute('SELECT session_id, enrollment, status, distance_m, timestamp FROM attendance;')
for row in cursor.fetchall():
    print(row)

# Notices
print('\n--- NOTICES ---')
cursor.execute('SELECT id, title, created_at FROM notices;')
for row in cursor.fetchall():
    print(row)

# Issues
print('\n--- ISSUES ---')
cursor.execute('SELECT id, title, category, status FROM issues;')
for row in cursor.fetchall():
    print(row)

# Events
print('\n--- EVENTS ---')
cursor.execute('SELECT id, title, event_date FROM events;')
for row in cursor.fetchall():
    print(row)

print('\n' + '='*60)
conn.close()
