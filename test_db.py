import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect('app.db')

# Create a cursor object
cursor = connection.cursor()

# Execute a query to fetch data from a table (replace 'your_table' with the actual table name)
cursor.execute("SELECT * FROM users")

# Fetch all results
results = cursor.fetchall()

# Print the results
for row in results:
    print(row)

# Close the connection
connection.close()