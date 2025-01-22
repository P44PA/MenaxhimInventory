import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import re


conn = sqlite3.connect('school_inventory_gui.db')
cursor = conn.cursor()


def is_valid_input(text, allowed_pattern=r'^[\w\s]+$'):  # Alphanumeric and spaces by default
    """Checks if the input text matches the allowed pattern."""
    if not text:  # Check for empty strings
        return False
    return re.fullmatch(allowed_pattern, text) is not None


def view_items(location_name=None, search_text=None):
    # Clear the current items from the treeview
    for row in item_table.get_children():
        item_table.delete(row)

    # Create the base query for selecting items
    query = '''
        SELECT items.name, items.category, items.quantity,
               items.status, locations.name, items.id
        FROM items
        JOIN locations ON items.location_id = locations.id
    '''

    # Apply location filter if a specific location is selected
    if location_name and location_name != "All Locations":
        query += " WHERE locations.name = ?"
        cursor.execute(query, (location_name,))
    else:
        cursor.execute(query)

    all_items = cursor.fetchall()

    # Filter the items based on the search text for item name or category
    filtered_items = []
    for item in all_items:
        item_name = item[0].lower()
        item_category = item[1].lower()

        if search_text and search_text.lower() not in item_name and search_text.lower() not in item_category:
            continue

        filtered_items.append(item)

    # Insert filtered items into the Treeview
    for item in filtered_items:
        if item[3] == "Damaged":
            item_table.insert('', 'end', values=item[:5], tags=('damaged',))
            item_table.tag_configure('damaged', background='red')
        elif item[3] == "For Repair":
            item_table.insert('', 'end', values=item[:5], tags=('for_repair',))
            item_table.tag_configure('for_repair', background='yellow')
        elif item[3] == "Usable":
            item_table.insert('', 'end', values=item[:5], tags=('usable',))
            item_table.tag_configure('usable', background='light green')
        else:
            item_table.insert('', 'end', values=item[:5])

    # update_usable_quantity(filtered_items)


# def update_usable_quantity(filtered_items):
#     usable_quantity = 0
#     for item in filtered_items:
#         if item[3] == "Usable":
#             usable_quantity += item[2]
#         if item[3] != "Usable":
#             usable_quantity -= item[2]
#     display_usable_quantity = max(usable_quantity , 0)
#     usable_quantity_label.config(text=f"Usable Quantity: {display_usable_quantity }")


def fetch_items_view(*args):
    location_name = location_var_view.get()
    search_text = search_entry.get()
    # if location_name != None:
    #     usable_quantity_label.pack_forget()
    # if search_text:
    #     usable_quantity_label.pack(pady=(0, 10))
    view_items(location_name, search_text)


def configure_treeview(tree):
    tree.config(style="mystyle.Treeview")
    tree.column("#0", width=0, stretch=tk.NO)
    for col in tree["columns"]:
        tree.column(col, anchor=tk.CENTER)


# Main Application Window
app = tk.Tk()
app.title("Sistem Inventari Gjergj Canco ")
app.resizable(False, False)

# Style Configuration
style = ttk.Style()
style.theme_create("mystyle", parent="alt", settings={
    "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
    "TNotebook.Tab": {"configure": {"padding": [5, 2]}},
    "Treeview": {"configure": {"background": "#f0f0f0", "rowheight": 25, "fieldbackground": "#f0f0f0"}},
    "Treeview.Heading": {"configure": {"background": "#ddd", "font": ('Helvetica', 10, 'bold')}},
})
style.theme_use("mystyle")

# Frame 3: View Items
frame_view = tk.Frame(app)
frame_view.pack(fill=tk.BOTH, expand=True)

# Title
tk.Label(frame_view, text="Item Inventory", font=('Helvetica', 14)).pack(pady=(10, 5))

# Search Entry for filtering items
search_entry = ttk.Entry(frame_view)  # Search Entry
search_entry.pack(pady=(0, 10), padx=10, fill=tk.X)
search_entry.bind("<KeyRelease>", lambda event: fetch_items_view())  # Bind to KeyRelease

# Location Dropdown for filtering items by location
location_var_view = tk.StringVar()
location_dropdown_view = ttk.OptionMenu(frame_view, location_var_view, "")
location_dropdown_view.pack(pady=(0, 10), padx=10, fill=tk.X)
location_var_view.trace("w", fetch_items_view)

# Treeview for displaying items
item_table = ttk.Treeview(frame_view, columns=("Name", "Category", "Quantity", "Status", "Location"), show="headings")
item_table.heading("Name", text="Item Name")
item_table.heading("Category", text="Category")
item_table.heading("Quantity", text="Quantity")
item_table.heading("Status", text="Status")
item_table.heading("Location", text="Location")
item_table.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)
configure_treeview(item_table)

# Usable Quantity Label


# Initialize the application (Ensure database tables and location data exist)
cursor.execute('SELECT id, name FROM locations')
locations = cursor.fetchall()
location_var_view.set("All Locations")  # Set default location to "All Locations"
location_dropdown_view['menu'].delete(0, 'end')
location_dropdown_view['menu'].add_command(label="All Locations",
                                           command=lambda: location_var_view.set("All Locations"))

if locations:
    for loc in locations:
        location_dropdown_view['menu'].add_command(label=loc[1],
                                                   command=lambda loc_name=loc[1]: location_var_view.set(loc_name))
    location_dropdown_view.config(state=tk.NORMAL)
else:
    location_var_view.set("")
    location_dropdown_view.config(state=tk.DISABLED)

# Fetch initial items to display
view_items()

# Start the application
app.mainloop()
