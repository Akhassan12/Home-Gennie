import os
import psycopg2
from tabulate import tabulate
from werkzeug.security import generate_password_hash

class DatabaseEditor:
    def __init__(self):
        database_url = os.environ.get('DATABASE_URL', 'sqlite:///instance/ar_interior.db')

        if database_url.startswith('postgresql'):
            # PostgreSQL connection
            self.is_postgresql = True
            params = {
                'host': 'localhost',
                'port': 5432,
                'database': 'ar_interior_db',
                'user': 'postgres',
                'password': 'password'
            }

            # Parse connection string if provided
            if '://' in database_url:
                # Format: postgresql://username:password@host:port/database
                parts = database_url.replace('postgresql://', '').split('@')
                if len(parts) == 2:
                    credentials = parts[0].split(':')
                    host_port_db = parts[1].split(':')
                    if len(credentials) == 2 and len(host_port_db) >= 2:
                        params['user'] = credentials[0]
                        params['password'] = credentials[1]
                        params['host'] = host_port_db[0]
                        params['port'] = int(host_port_db[1])
                        params['database'] = host_port_db[2] if len(host_port_db) > 2 else 'ar_interior_db'

            try:
                self.conn = psycopg2.connect(**params)
                self.cursor = self.conn.cursor()
                self.tables = ['user', 'project', 'budget', 'wishlist_item', 'feedback']
            except psycopg2.Error as e:
                print(f"PostgreSQL connection failed: {e}")
                print("Falling back to SQLite...")
                self.is_postgresql = False
                self._setup_sqlite()
        else:
            # SQLite fallback
            self.is_postgresql = False
            self._setup_sqlite()

    def _setup_sqlite(self):
        """Setup SQLite connection"""
        import sqlite3
        db_path = 'instance/ar_interior.db'
        os.makedirs('instance', exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.tables = ['user', 'project', 'budget', 'wishlist_item', 'feedback']

    def get_columns(self, table):
        if self.is_postgresql:
            self.cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            return [column[0] for column in self.cursor.fetchall()]
        else:
            self.cursor.execute(f"PRAGMA table_info({table})")
            return [column[1] for column in self.cursor.fetchall()]

    def view_table(self, table_name):
        try:
            return self._extracted_from_view_table_3(table_name)
        except Exception as e:
            print(f"Error viewing table: {e}")
            input("Press Enter to continue...")
            return [], []

    # TODO Rename this here and in `view_table`
    def _extracted_from_view_table_3(self, table_name):
        columns = self.get_columns(table_name)
        self.cursor.execute(f"SELECT * FROM {table_name}")
        rows = self.cursor.fetchall()
        if rows:
            print(f"\n=== {table_name.upper()} Table ===")
            print(tabulate(rows, headers=columns, tablefmt='grid'))
            print(f"Total records: {len(rows)}\n")
        else:
            print(f"\nNo records found in {table_name} table.\n")

        input("Press Enter to continue...")  # Pause to view the results
        return rows, columns

    def get_column_value(self, col):
        """Get value for a column based on its type"""
        if col == 'password_hash':
            return generate_password_hash(input("Enter password for user: "))
        elif col == 'is_verified':
            return input("Is user verified? (yes/no): ").lower() == 'yes'
        else:
            return input(f"Enter {col}: ")

    def add_record(self, table_name):
        columns = self.get_columns(table_name)
        values = []
        print(f"\nAdding new record to {table_name}")

        for col in columns:
            if col == 'id':  # Skip ID column as it's auto-generated
                continue
            if col.endswith('_at'):  # Skip timestamp columns
                continue
            values.append(self.get_column_value(col))

        cols = ','.join([c for c in columns if c != 'id' and not c.endswith('_at')])

        if self.is_postgresql:
            placeholders = ','.join(['%s' for _ in range(len(values))])
        else:
            placeholders = ','.join(['?' for _ in range(len(values))])

        try:
            self.cursor.execute(f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})", values)
            self.conn.commit()
            print("Record added successfully!")
        except Exception as e:
            print(f"Error adding record: {e}")

    def delete_record(self, table_name):
        self.view_table(table_name)
        record_id = input("\nEnter the ID of the record to delete: ")

        try:
            if self.is_postgresql:
                self.cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (record_id,))
            else:
                self.cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))

            if self.cursor.rowcount > 0:
                self.conn.commit()
                print("Record deleted successfully!")
            else:
                print("No record found with that ID.")
        except Exception as e:
            print(f"Error deleting record: {e}")

    def edit_record(self, table_name):
        rows, columns = self.view_table(table_name)
        if not rows:
            return

        record_id = input("\nEnter the ID of the record to edit: ")
        if self.is_postgresql:
            self.cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
        else:
            self.cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
        record = self.cursor.fetchone()

        if not record:
            print("No record found with that ID.")
            return

        print("\nCurrent values:")
        for col, val in zip(columns, record):
            print(f"{col}: {val}")

        print("\nEnter new values (press Enter to keep current value):")
        updates = []
        values = []

        for col, current_val in zip(columns, record):
            if col in ['id', 'created_at']:  # Skip ID and timestamp
                continue

            # Determine placeholder based on database type
            placeholder = '%s' if self.is_postgresql else '?'

            if col == 'password_hash':
                if (new_val := input("Enter new password (Enter to skip): ")):
                    updates.append(f"{col} = {placeholder}")
                    values.append(generate_password_hash(new_val))
            elif col == 'is_verified':
                if (new_val := input("Is user verified? (yes/no/Enter to skip): ").lower()) in ['yes', 'no']:
                    updates.append(f"{col} = {placeholder}")
                    values.append(new_val == 'yes')
            else:
                if (new_val := input(f"Enter new {col} (Enter to skip): ")):
                    updates.append(f"{col} = {placeholder}")
                    values.append(new_val)

        if not updates:
            print("No changes made.")
            return

        # Add ID for WHERE clause
        values.append(record_id)
        id_placeholder = '%s' if self.is_postgresql else '?'
        update_sql = f"UPDATE {table_name} SET {', '.join(updates)} WHERE id = {id_placeholder}"

        try:
            self.cursor.execute(update_sql, values)
            self.conn.commit()
            print("Record updated successfully!")
        except Exception as e:
            print(f"Error updating record: {e}")

    def main_menu(self):
        while True:
            try:
                print("\nAR Interior Dashboard Database Editor")
                print("====================================")
                print("1. View table")
                print("2. Add record")
                print("3. Edit record")
                print("4. Delete record")
                print("0. Exit")
                
                choice = input("\nEnter your choice (0-4): ")
                
                if choice == '0':
                    break
                
                if choice in ['1', '2', '3', '4']:
                    print("\nSelect table:")
                    for i, table in enumerate(self.tables, 1):
                        print(f"{i}. {table}")
                    
                    try:
                        table_index = int(input("\nEnter table number: ")) - 1
                        if 0 <= table_index < len(self.tables):
                            table_name = self.tables[table_index]
                            if choice == '1':
                                self.view_table(table_name)
                            elif choice == '2':
                                self.add_record(table_name)
                            elif choice == '3':
                                self.edit_record(table_name)
                            elif choice == '4':
                                self.delete_record(table_name)
                        else:
                            print("Invalid table number!")
                            input("Press Enter to continue...")
                    except ValueError:
                        print("Please enter a valid number!")
                        input("Press Enter to continue...")
                else:
                    print("Invalid choice! Please enter a number between 0 and 4.")
                    input("Press Enter to continue...")
            except Exception as e:
                print(f"An error occurred: {e}")
                input("Press Enter to continue...")

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    editor = DatabaseEditor()
    editor.main_menu()
