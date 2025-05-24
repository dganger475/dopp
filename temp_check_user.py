import sqlite3

# Connect to the database
conn = sqlite3.connect("faces.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Query the users table for the realkeed user
cursor.execute("SELECT * FROM users WHERE username = 'realkeed'")
user = cursor.fetchone()

if user:
    print("User found:")
    for key in user.keys():
        print(f"{key}: {user[key]}")
else:
    print("User 'realkeed' not found in the database")

# Close the connection
conn.close()
