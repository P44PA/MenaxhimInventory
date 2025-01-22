
import re
from Creator import *

# Database setup
conn = sqlite3.connect('school_inventory_gui.db')
cursor = conn.cursor()

def is_valid_email(email):
    # Simple regex to check if email is valid
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def is_valid_phone(phone):
    # Simple regex to check if phone number contains only digits and has a specific length (e.g., 10 digits)
    return bool(re.match(r"^\d{10}$", phone))


def is_supplier_exists(supplier_name, contact_email):
    cursor.execute("SELECT * FROM suppliers WHERE supplier_name = ? OR contact_email = ?",
                   (supplier_name, contact_email))
    return cursor.fetchone() is not None


def is_valid_input(text, allowed_pattern=r'^[\w\s-]+$'):
    if not text:
        return False
    return re.fullmatch(allowed_pattern, text) is not None
