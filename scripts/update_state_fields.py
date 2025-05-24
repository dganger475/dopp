import sqlite3

# Path to your database
DB_PATH = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"

# Keyword to state mappings
keyword_state_map = {
    "highpoint": "NC",
    "HOLMES": "MS",
    "Maryland": "MD",
    "Ryne": "NC",
    "Manhatton": "NY",
    "Mary": "WA",
    "feyetville": "NC",
    "marshill": "NC",
    "NorthCarolina": "NC",
    "Mississippi": "MS",
    "Wake": "NC",
    "Davidson": "NC",
    "Merideth": "NC",
    "Methodist Univer": "NC",
    "Alemeda": "CA",
    "Millis": "MA",
    "Ohio": "OH",
    "Queens": "NY",
    "Saint Leo": "FL",
    "Francis": "NY",
    "Livingston": "NC",
    "Wlhi": "OR",
    "bridgeway": "MA",
    "johnjay": "NY",
    "whitmanhanson": "OR",
    "Patterson": "NJ",
    "wohelo": "MS",
    "yale": "CT",
    "Astoria": "OR",
    "Oregon": "OR",
    "Austin": "TX",
    "fox": "OR",
    "PHS": "OR",
    "uschist": "CA",
}

def update_state_fields():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, filename FROM faces")
    rows = cursor.fetchall()

    updated_count = 0

    for row_id, filename in rows:
        for keyword, state in keyword_state_map.items():
            if keyword.lower() in filename.lower():
                cursor.execute("UPDATE faces SET state = ? WHERE id = ?", (state, row_id))
                updated_count += 1
                break  # Stop after first match for performance and prevent multiple overwrites

    conn.commit()
    conn.close()

    print(f"✅ Updated state field for {updated_count} entries in the database.")

if __name__ == "__main__":
    update_state_fields()
