import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from src.utils.logger import logger
from src.config import config
from src.models import Property

class DatabaseRepository:
    """Repository for all SQLite interactions."""
    
    def __init__(self, db_path: str = config.DB_NAME):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Helper to get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes the database schema if it doesn't exist."""
        logger.info(f"Checking database initialization at {self.db_path}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    bank_name TEXT,
                    reserve_price REAL,
                    emd REAL,
                    area_sqft REAL,
                    rate_sqft REAL,
                    city TEXT,
                    area_locality TEXT,
                    state TEXT,
                    auction_start_date TEXT,
                    auction_end_time TEXT,
                    borrower_name TEXT,
                    notice_image_url TEXT,
                    source_url TEXT UNIQUE,
                    description TEXT,
                    listing_summary TEXT,
                    market_rate_sqft REAL,
                    discount_rate_percent REAL,
                    village TEXT,
                    property_type TEXT,
                    floor TEXT,
                    society_name TEXT,
                    auction_id TEXT,
                    contact_details TEXT,
                    branch_name TEXT,
                    service_provider TEXT,
                    asset_category TEXT,
                    auction_type TEXT,
                    application_submission_date TEXT,
                    possession_status TEXT,
                    investment_score INTEGER,
                    risk_rating TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'User',
                    is_active BOOLEAN DEFAULT 1,
                    allowed_cities TEXT,
                    allowed_columns TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    cities TEXT,
                    plan_type TEXT,
                    amount REAL,
                    transaction_id TEXT,
                    start_date TEXT,
                    expiry_date TEXT,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create premium admin if not exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'IronLedger_X81'")
            if cursor.fetchone()[0] == 0:
                import hashlib
                admin_pass = hashlib.sha256("Q!9rZ$M@8P#2xkWf".encode()).hexdigest()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, allowed_cities, allowed_columns)
                    VALUES (?, ?, ?, ?, ?)
                """, ("IronLedger_X81", admin_pass, "Admin", "*", "*"))

            # Create default admin if not exists (Legacy)
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            if cursor.fetchone()[0] == 0:
                import hashlib
                admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, allowed_cities, allowed_columns)
                    VALUES (?, ?, ?, ?, ?)
                """, ("admin", admin_pass, "Admin", "*", "*"))

            
            # Migration: Add missing columns if they don't exist
            cursor.execute("PRAGMA table_info(properties)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            columns_to_ensure = {
                'auction_id': 'TEXT',
                'contact_details': 'TEXT',
                'branch_name': 'TEXT',
                'service_provider': 'TEXT',
                'asset_category': 'TEXT',
                'auction_type': 'TEXT',
                'application_submission_date': 'TEXT',
                'possession_status': 'TEXT',
                'investment_score': 'INTEGER',
                'risk_rating': 'TEXT',
                'crawled_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            for col_name, col_type in columns_to_ensure.items():
                if col_name not in existing_columns:
                    logger.info(f"Migrating: Adding column {col_name} to properties table")
                    cursor.execute(f"ALTER TABLE properties ADD COLUMN {col_name} {col_type}")

            # Migration: ensure users.is_active exists for login checks
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [col[1] for col in cursor.fetchall()]
            if 'is_active' not in user_columns:
                logger.info("Migrating: Adding column is_active to users table")
                cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
                cursor.execute("UPDATE users SET is_active = 1 WHERE is_active IS NULL")

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_properties_source_url ON properties(source_url)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_properties_auction_id ON properties(auction_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_properties_market_rate ON properties(market_rate_sqft)"
            )
            
            conn.commit()

    @staticmethod
    def _parse_db_datetime(value) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def _row_to_property(self, row: sqlite3.Row) -> Property:
        """Convert a DB row to Property, ignoring non-model columns."""
        data = dict(row)
        for extra in ("is_active", "created_at"):
            data.pop(extra, None)
        parsed = self._parse_db_datetime(data.get("crawled_at"))
        if parsed is not None:
            data["crawled_at"] = parsed
        return Property.model_validate(data)

    def _find_existing_id(self, cursor, prop: Property) -> Optional[int]:
        cursor.execute("SELECT id FROM properties WHERE source_url = ?", (prop.source_url,))
        row = cursor.fetchone()
        if row:
            return row["id"]

        if prop.auction_id and prop.auction_id != "N/A":
            cursor.execute("SELECT id FROM properties WHERE auction_id = ?", (prop.auction_id,))
            row = cursor.fetchone()
            if row:
                return row["id"]

        cursor.execute(
            """
            SELECT id FROM properties
            WHERE title = ? AND bank_name = ? AND reserve_price = ?
            """,
            (prop.title, prop.bank_name, prop.reserve_price),
        )
        row = cursor.fetchone()
        return row["id"] if row else None

    def _upsert_property(self, cursor, prop: Property) -> bool:
        """Insert or update one property. Returns True if inserted."""
        data = prop.model_dump(exclude={"id"})
        existing_id = self._find_existing_id(cursor, prop)
        columns = list(data.keys())

        if existing_id:
            update_data = {k: v for k, v in data.items() if k != "crawled_at"}
            set_clause = ", ".join([f"{col} = ?" for col in update_data.keys()])
            sql = f"UPDATE properties SET {set_clause}, crawled_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(sql, list(update_data.values()) + [existing_id])
            return False

        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO properties ({', '.join(columns)}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
        return True

    def save_property(self, prop: Property) -> bool:
        """Saves or updates a property in the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                inserted = self._upsert_property(cursor, prop)
                conn.commit()
                action = "Inserted" if inserted else "Updated"
                logger.debug(f"{action} property: {prop.source_url}")
                return True
        except Exception as e:
            logger.error(f"Error saving property {prop.source_url}: {e}")
            return False

    def save_properties_batch(self, properties: List[Property]) -> int:
        """Saves a batch of properties efficiently and returns the number of newly inserted properties."""
        if not properties:
            return 0

        new_insert_count = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for prop in properties:
                    if self._upsert_property(cursor, prop):
                        new_insert_count += 1
                conn.commit()
                return new_insert_count
        except Exception as e:
            logger.error(f"Error during batch save: {e}")
            return 0


    def get_property_count(self) -> int:
        """Returns the total count of properties in the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM properties")
                return cursor.fetchone()['count']
        except Exception as e:
            logger.error(f"Error getting property count: {e}")
            return 0

    def get_all_properties(self, limit: Optional[int] = None) -> List[Property]:
        """Retrieves all properties from the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Use CASE to handle N/A dates if we want to sort correctly, but for now crawled_at is reliable
                sql = "SELECT * FROM properties ORDER BY crawled_at DESC"
                if limit:
                    sql += f" LIMIT {limit}"
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [self._row_to_property(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching properties: {e}")
            return []

    def get_last_crawl_date(self) -> Optional[datetime]:
        """Returns the date of the most recent crawl."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(crawled_at) as last_crawl FROM properties")
                row = cursor.fetchone()
                if row and row['last_crawl']:
                    return self._parse_db_datetime(row['last_crawl'])
                return None
        except Exception as e:
            logger.error(f"Error getting last crawl date: {e}")
            return None

    def get_pending_enrichment(self) -> List[Property]:
        """Retrieves properties that need AI enrichment."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM properties WHERE market_rate_sqft IS NULL ORDER BY crawled_at DESC"
                )
                rows = cursor.fetchall()
                return [self._row_to_property(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching pending enrichments: {e}")
            return []

    def update_enrichment(self, prop_id: int, enrichment_data: Dict[str, Any]) -> bool:
        """Updates a property with enriched data."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update statement dynamically
                set_clause = ', '.join([f"{k} = ?" for k in enrichment_data.keys()])
                sql = f"UPDATE properties SET {set_clause} WHERE id = ?"
                
                params = list(enrichment_data.values()) + [prop_id]
                cursor.execute(sql, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating enrichment for ID {prop_id}: {e}")
            return False

    def get_existing_fingerprints(self) -> set:
        """Returns a set of (auction_id, title, bank_name, reserve_price) for all properties."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT auction_id, title, bank_name, reserve_price FROM properties")
            return {
                (row['auction_id'], row['title'], row['bank_name'], row['reserve_price']) 
                for row in cursor.fetchall()
            }

    # --- User Management Methods ---

    def verify_user(self, username, password) -> Optional[Dict[str, Any]]:
        """Verifies user credentials and returns user info if valid."""
        import hashlib
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM users 
                    WHERE username = ? AND password_hash = ? AND is_active = 1
                """, (username, pwd_hash))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Retrieves all users from the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []

    def save_user(self, user_data: Dict[str, Any]) -> bool:
        """Creates or updates a user."""
        try:
            import hashlib
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if updating or creating
                username = user_data['username']
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                
                if row:
                    # Update (excluding password if not provided)
                    user_id = row['id']
                    fields = {k: v for k, v in user_data.items() if k not in ['id', 'username', 'password']}
                    if 'password' in user_data and user_data['password']:
                        fields['password_hash'] = hashlib.sha256(user_data['password'].encode()).hexdigest()
                    
                    if fields:
                        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
                        cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", list(fields.values()) + [user_id])
                else:
                    # Create
                    pwd_hash = hashlib.sha256(user_data['password'].encode()).hexdigest()
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, role, allowed_cities, allowed_columns)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username, pwd_hash, user_data.get('role', 'User'), 
                          user_data.get('allowed_cities', ''), user_data.get('allowed_columns', '')))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            return False

    def delete_user(self, username: str) -> bool:
        """Deletes a user from the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

    def create_subscription(self, user_id: int, sub_data: Dict[str, Any]) -> bool:
        """Records a new subscription and updates user permissions."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Insert subscription record
                cursor.execute("""
                    INSERT INTO subscriptions (user_id, cities, plan_type, amount, transaction_id, start_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, sub_data['cities'], sub_data['plan_type'], sub_data['amount'], 
                      sub_data['transaction_id'], sub_data['start_date'], sub_data['expiry_date']))
                
                # Fetch existing allowed_cities
                cursor.execute("SELECT allowed_cities FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                current_cities = set([c.strip() for c in row['allowed_cities'].split(',') if c.strip()]) if row else set()
                
                # Add new cities
                new_cities = [c.strip() for c in sub_data['cities'].split(',') if c.strip()]
                for city in new_cities:
                    current_cities.add(city)
                
                # Update user permissions
                updated_cities = ",".join(list(current_cities))
                cursor.execute("UPDATE users SET allowed_cities = ? WHERE id = ?", (updated_cities, user_id))
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return False

    def get_user_subscriptions(self, user_id: Optional[int]) -> List[Dict[str, Any]]:
        """Fetches all subscriptions for a user."""
        if user_id is None:
            return []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subscriptions WHERE user_id = ? ORDER BY expiry_date DESC", (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching subscriptions: {e}")
            return []

    def get_id_by_username(self, username: str) -> Optional[int]:
        """Gets user ID from username."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                return row['id'] if row else None
        except Exception as e:
            logger.error(f"Error getting user ID: {e}")
            return None
