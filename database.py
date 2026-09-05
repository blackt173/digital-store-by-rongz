import sqlite3

# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect('digital_shop.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  balance REAL DEFAULT 0,
                  language TEXT DEFAULT 'km',
                  is_admin INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT (datetime('now', '+7 hours')))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  price REAL NOT NULL,
                  stock INTEGER DEFAULT 0,
                  category TEXT,
                  auto_delete_days INTEGER DEFAULT 0,
                  subscription_days INTEGER DEFAULT 0,
                  is_active INTEGER DEFAULT 1,
                  created_at TIMESTAMP DEFAULT (datetime('now', '+7 hours')))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS digital_products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER NOT NULL,
                  email TEXT NOT NULL,
                  password TEXT NOT NULL,
                  license_key TEXT,
                  twofa_secret TEXT,
                  is_sold INTEGER DEFAULT 0,
                  sold_to INTEGER,
                  sold_at TIMESTAMP,
                  order_id INTEGER,
                  expiry_date TIMESTAMP,
                  reminder_sent INTEGER DEFAULT 0,
                  FOREIGN KEY (product_id) REFERENCES products (id),
                  FOREIGN KEY (sold_to) REFERENCES users (user_id),
                  FOREIGN KEY (order_id) REFERENCES orders (id))'''
    
    c.execute('''CREATE TABLE IF NOT EXISTS cart
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  product_id INTEGER NOT NULL,
                  quantity INTEGER DEFAULT 1,
                  added_at TIMESTAMP DEFAULT (datetime('now', '+7 hours')),
                  FOREIGN KEY (user_id) REFERENCES users (user_id),
                  FOREIGN KEY (product_id) REFERENCES products (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  product_id INTEGER NOT NULL,
                  transaction_id TEXT UNIQUE NOT NULL,
                  amount REAL NOT NULL,
                  quantity INTEGER DEFAULT 1,
                  payment_status TEXT DEFAULT 'pending',
                  khqr_data TEXT,
                  qr_image_path TEXT,
                  qr_expiry TIMESTAMP,
                  bakong_transaction_id TEXT,
                  created_at TIMESTAMP DEFAULT (datetime('now', '+7 hours')),
                  completed_at TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (user_id),
                  FOREIGN KEY (product_id) REFERENCES products (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS payment_verifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  order_id INTEGER NOT NULL,
                  transaction_id TEXT UNIQUE NOT NULL,
                  md5_hash TEXT,
                  bakong_transaction_id TEXT,
                  verification_attempts INTEGER DEFAULT 0,
                  last_checked TIMESTAMP,
                  status TEXT DEFAULT 'pending',
                  FOREIGN KEY (order_id) REFERENCES orders (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS feedbacks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  product_id INTEGER NOT NULL,
                  rating INTEGER NOT NULL,
                  comment TEXT,
                  created_at TIMESTAMP DEFAULT (datetime('now', '+7 hours')),
                  FOREIGN KEY (user_id) REFERENCES users (user_id),
                  FOREIGN KEY (product_id) REFERENCES products (id))''')
    
    try:
        c.execute("ALTER TABLE payment_verifications ADD COLUMN md5_hash TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE orders ADD COLUMN quantity INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE digital_products ADD COLUMN order_id INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN auto_delete_days INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'km'")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN is_active INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN subscription_days INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE digital_products ADD COLUMN expiry_date TIMESTAMP")
        c.execute("ALTER TABLE digital_products ADD COLUMN reminder_sent INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

# ============ DATABASE HELPER CLASS ============
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('digital_shop.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
    
    def commit(self):
        self.conn.commit()
