import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import re
from Creator import *
from Functions import *

# Database setup
conn = sqlite3.connect('school_inventory_gui.db')
cursor = conn.cursor()

create_all_tables()

def add_location():
    location_name = location_entry.get().strip()

    if not is_valid_input(location_name):
        messagebox.showerror("Input Error", "Location name can only contain alphanumeric characters and spaces.")
        return

    try:
        cursor.execute('INSERT INTO locations (name) VALUES (?)', (location_name,))
        conn.commit()
        messagebox.showinfo("Success", "Location added successfully!")
        update_location_dropdown()
        view_locations()
        location_entry.delete(0, tk.END)

    except sqlite3.IntegrityError:
        messagebox.showerror("Duplicate Error", "A location with this name already exists.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"A database error occurred: {e}")
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")


def delete_location():
    selected = location_table.selection()
    if not selected:
        messagebox.showwarning("Selection Required", "Please select a location to delete.")
        return

    location_name = location_table.item(selected[0])['values'][0]

    # Apply a tag to change the color of the selected row to 'lightblue'
    location_table.tag_configure('selected', background='lightblue')
    location_table.item(selected[0], tags='selected')

    if not messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete '{location_name}'?\nThis will also delete all items in this location!"):
        # Reset the row color if the user cancels the delete action
        location_table.item(selected[0], tags='')
        return

    try:
        cursor.execute('SELECT id FROM locations WHERE name = ?', (location_name,))
        location_id = cursor.fetchone()[0]

        cursor.execute('DELETE FROM items WHERE location_id = ?', (location_id,))
        cursor.execute('DELETE FROM locations WHERE id = ?', (location_id,))
        conn.commit()

        messagebox.showinfo("Success", "Location and associated items deleted successfully!")
        view_locations()
        update_location_dropdown()
        view_items()
    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Database Error", f"A database error occurred: {e}")
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")


def view_locations():
    for row in location_table.get_children():
        location_table.delete(row)
    cursor.execute('SELECT * FROM locations')
    for location in cursor.fetchall():
        location_table.insert('', 'end', values=(location[1],))


def update_location_dropdown():
    cursor.execute('SELECT id, name FROM locations')
    locations = cursor.fetchall()

    location_dropdown['menu'].delete(0, 'end')
    if locations:
        for loc in locations:
            location_dropdown['menu'].add_command(label=loc[1],
                                                  command=lambda loc_name=loc[1]: location_var_add_item.set(loc_name))
        location_var_add_item.set(locations[0][1])
        location_dropdown.config(state=tk.NORMAL)
    else:
        location_var_add_item.set("")
        location_dropdown.config(state=tk.DISABLED)

    location_dropdown_view['menu'].delete(0, 'end')
    location_dropdown_view['menu'].add_command(label="All Locations",
                                               command=lambda: location_var_view.set("All Locations"))
    if locations:
        for loc in locations:
            location_dropdown_view['menu'].add_command(label=loc[1],
                                                       command=lambda loc_name=loc[1]: location_var_view.set(loc_name))
        location_var_view.set("All Locations")
        location_dropdown_view.config(state=tk.NORMAL)
    else:
        location_var_view.set("")
        location_dropdown_view.config(state=tk.DISABLED)


def add_item():
    name = name_entry.get().strip()
    category = category_var.get()
    status = status_var.get()
    location_name = location_var_add_item.get()

    if not is_valid_input(name):
        messagebox.showerror("Input Error", "Item name can only contain alphanumeric characters and spaces.")
        return

    if not category or category == "Category N/A":
        messagebox.showerror("Input Error", "Please select a category.")
        return

    if not location_name:
        messagebox.showerror("Input Error", "Please select a location.")
        return

    try:
        quantity_str = quantity_entry.get()
        if not quantity_str:
            raise ValueError("Quantity cannot be empty.")
        quantity = int(quantity_str)
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        cursor.execute('SELECT id FROM locations WHERE name = ?', (location_name,))
        location_result = cursor.fetchone()
        if location_result:
            location_id = location_result[0]

            cursor.execute('SELECT quantity FROM items WHERE name = ? AND location_id = ? AND status = ?',
                           (name, location_id, status))
            existing_item = cursor.fetchone()

            if existing_item:
                new_quantity = existing_item[0] + quantity
                cursor.execute('''UPDATE items SET quantity = ? WHERE name = ? AND location_id = ? AND status = ?''',
                               (new_quantity, name, location_id, status))
                conn.commit()
                messagebox.showinfo("Success", "Item quantity updated successfully!")
            else:
                cursor.execute('''INSERT INTO items (name, category, quantity, status, location_id)
                                  VALUES (?, ?, ?, ?, ?)''', (name, category, quantity, status, location_id))
                conn.commit()
                messagebox.showinfo("Success", "Item added successfully!")

            view_items(location_name)
            name_entry.delete(0, tk.END)
            quantity_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Input Error", "Selected location not found.")
    except ValueError as e:
        messagebox.showerror("Input Error", f"Invalid quantity: {e}")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"A database error occurred: {e}")
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")


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
        if item[3] == "damaged":
            item_table.insert('', 'end', values=item[:5], tags=('damaged',))
            item_table.tag_configure('damaged', background='red')
        elif item[3] == "for repair":
            item_table.insert('', 'end', values=item[:5], tags=('for_repair',))
            item_table.tag_configure('for_repair', background='yellow')
        elif item[3] == "usable":
            item_table.insert('', 'end', values=item[:5], tags=('usable',))
            item_table.tag_configure('usable', background='light green')
        else:
            item_table.insert('', 'end', values=item[:5])




def fetch_items_view(*args):
    location_name = location_var_view.get()
    search_text = search_entry.get()

    view_items(location_name, search_text)


def configure_treeview(tree):
    tree.config(style="mystyle.Treeview")
    tree.column("#0", width=0, stretch=tk.NO)
    for col in tree["columns"]:
        tree.column(col, anchor=tk.CENTER)


def reset_add_item_form():
    name_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)
    status_var.set("usable")
    location_var_add_item.set("")
    category_var.set(category_options[0])


def on_tab_change(event):
    if notebook.index(notebook.select()) == 1:
        reset_add_item_form()


# Main Application Window
app = tk.Tk()
app.title("Sistem Inventari Gjergj Canco")
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

# Predefined category options
category_options = ['Category N/A', "Artikuj Shkolle", "Paisje Klase", "Tech", "Paisje Sportive", "Libra", "Mirmbajtje",
                    "Te tjera"]
category_var = tk.StringVar()
category_var.set(category_options[0])

# Notebook for Tabs
notebook = ttk.Notebook(app)
frame_location = tk.Frame(notebook)
frame_item = tk.Frame(notebook)
frame_view = tk.Frame(notebook)

notebook.add(frame_location, text="Locations")
notebook.add(frame_item, text="Add Items")
notebook.add(frame_view, text="View Items")
notebook.pack(fill=tk.BOTH, expand=True)

# Frame 1: Location Management
tk.Label(frame_location, text="Manage Locations", font=('Helvetica', 14)).pack(pady=(10, 5))
location_label = tk.Label(frame_location, text="Enter location", font=('Helvetica', 10))
location_label.pack(padx=10, pady=(0, 5))
location_entry = ttk.Entry(frame_location)
location_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
add_loc_button = ttk.Button(frame_location, text="Add Location", command=add_location)
add_loc_button.pack(padx=10, pady=(0, 10), fill=tk.X)
delete_loc_button = ttk.Button(frame_location, text="Delete Location", command=delete_location)
delete_loc_button.pack(padx=10, pady=(0, 10), fill=tk.X)
location_table = ttk.Treeview(frame_location, columns=("Name"), show="headings")
location_table.heading("Name", text="Location Name")
location_table.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)
configure_treeview(location_table)

# Frame 2: Item Management
tk.Label(frame_item, text="Add New Item", font=('Helvetica', 14)).pack(pady=(10, 5))
name_label = tk.Label(frame_item, text="Enter item name", font=('Helvetica', 10))
name_label.pack(pady=(0, 5), padx=10)
name_entry = ttk.Entry(frame_item)
name_entry.pack(pady=(0, 5), padx=10, fill=tk.X)
quantity_label = tk.Label(frame_item, text="Enter quantity", font=('Helvetica', 10))
quantity_label.pack(pady=(0, 5), padx=10)
quantity_entry = ttk.Entry(frame_item)
quantity_entry.pack(pady=(0, 5), padx=10, fill=tk.X)

# State options
state_options = ["Status", "Usable", "Damaged", "For Repair"]
status_var = tk.StringVar()
status_var.set(state_options[0])

status_label = tk.Label(frame_item, text="Select status", font=('Helvetica', 10))
status_label.pack(pady=(0, 5), padx=10)
status_dropdown = ttk.OptionMenu(frame_item, status_var, *state_options)
status_dropdown.pack(pady=(0, 5), padx=10, fill=tk.X)

location_label_add_item = tk.Label(frame_item, text="Select location", font=('Helvetica', 10))
location_label_add_item.pack(pady=(0, 5), padx=10)
location_var_add_item = tk.StringVar()
location_dropdown = ttk.OptionMenu(frame_item, location_var_add_item, "")
location_dropdown.pack(pady=(0, 10), padx=10, fill=tk.X)

category_label = tk.Label(frame_item, text="Select item category", font=('Helvetica', 10))
category_label.pack(pady=(0, 5), padx=10)
category_dropdown = ttk.OptionMenu(frame_item, category_var, *category_options)
category_dropdown.pack(pady=(0, 5), padx=10, fill=tk.X)

add_item_button = ttk.Button(frame_item, text="Add Item", command=add_item)
add_item_button.pack(pady=(0, 10), padx=10, fill=tk.X)


# Frame 3: View Items
# Add this function for deleting an item from the table and database
def delete_item(item_table):
    selected_item = item_table.selection()  # Get the selected row
    if not selected_item:
        messagebox.showwarning("Selection Error", "No item selected!")
        return

    # Get the item details from the selected row
    item_name = item_table.item(selected_item, "values")[0]

    # Confirm deletion
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{item_name}'?")
    if not confirm:
        return


    cursor.execute("DELETE FROM items WHERE name = ?", (item_name,))
    conn.commit()

    # Remove the item from the Treeview
    item_table.delete(selected_item)



    # Success message
    messagebox.showinfo("Success", f"Item '{item_name}' deleted successfully!")


# Main frame configuration
tk.Label(frame_view, text="Item Inventory", font=('Helvetica', 14)).pack(pady=(10, 5))
search_entry = ttk.Entry(frame_view)
search_entry.pack(pady=(0, 5), padx=10, fill=tk.X)

location_var_view = tk.StringVar(value="All Locations")
location_dropdown_view = ttk.OptionMenu(frame_view, location_var_view, "All Locations")
location_dropdown_view.pack(pady=(0, 5), padx=10, fill=tk.X)

# Configure Treeview style to highlight the selected row with blue background
style = ttk.Style()
style.configure("Treeview", rowheight=25)
style.map(
    "Treeview",
    background=[("selected", "blue")],
    foreground=[("selected", "white")]
)

# Create the Treeview for displaying items
item_table = ttk.Treeview(
    frame_view, columns=("Name", "Category", "Quantity", "Status", "Location"),
    show="headings", style="Treeview"
)
item_table.heading("Name", text="Item Name")
item_table.heading("Category", text="Category")
item_table.heading("Quantity", text="Quantity")
item_table.heading("Status", text="Status")
item_table.heading("Location", text="Location")
item_table.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)

configure_treeview(item_table)


# Add a Delete Button
delete_button = tk.Button(
    frame_view, text="Delete Item", command=lambda: delete_item(item_table), bg="light grey", fg="black"
)
delete_button.pack(pady=(5, 10), padx=10)

def update_item_quantity(item_table):
    # Get the selected item
    selected_item = item_table.selection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "No item selected!")
        return

    # Extract the item's details
    item_details = item_table.item(selected_item, "values")
    item_name = item_details[0]  # Assuming the first column is the item name

    # Create a custom dialog for input
    def confirm_update():
        try:
            new_quantity = int(quantity_var.get())
            if new_quantity < 0:
                raise ValueError("Quantity cannot be negative!")

            # Update the database (replace 'items' with your table name)
            cursor.execute("UPDATE items SET quantity = ? WHERE name = ?", (new_quantity, item_name))
            conn.commit()

            # Update the Treeview with the new quantity
            item_values = list(item_details)
            item_values[2] = new_quantity  # Assuming the third column is quantity
            item_table.item(selected_item, values=item_values)

            # Close the dialog and show success message
            dialog.destroy()
            messagebox.showinfo("Success", f"Quantity for '{item_name}' updated to {new_quantity}!")

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

    # Create the dialog window
    dialog = tk.Toplevel()
    dialog.title("Update Quantity")
    dialog.geometry("300x150")
    dialog.transient()  # Make this window modal
    dialog.grab_set()

    tk.Label(dialog, text=f"Update quantity for '{item_name}'", font=('Helvetica', 12)).pack(pady=(10, 5))
    quantity_var = tk.StringVar()
    tk.Entry(dialog, textvariable=quantity_var, font=('Helvetica', 10)).pack(pady=(5, 5), padx=10)

    tk.Button(dialog, text="Update", command=confirm_update, bg="light grey").pack(pady=(10, 5))

    dialog.mainloop()


# Add Update Quantity Button
update_button = tk.Button(
    frame_view, text="Update Quantity", command=lambda: update_item_quantity(item_table), bg="light grey", fg="black"
)
update_button.pack(pady=(5, 10), padx=10)


# Event bindings
search_entry.bind("<KeyRelease>", lambda event: fetch_items_view())
location_var_view.trace("w", lambda *args: fetch_items_view())
notebook.bind("<<NotebookTabChanged>>", on_tab_change)


def add_user():
    name = user_name_entry.get().strip()
    psw = password_entry.get().strip()
    role = user_role_var.get()

    # Input validation
    if not is_valid_input(name):
        messagebox.showerror("Input Error", "User name can only contain alphanumeric characters and spaces.")
        return

    if not is_valid_input(psw):
        messagebox.showerror("Input Error", "Please enter a valid password.")
        return

    if not role:  # Check if role is selected
        messagebox.showerror("Input Error", "Please select a role.")
        return

    try:
        # Insert the new user into the database
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (name, psw, role))
        conn.commit()
        messagebox.showinfo("Success", f"{name} as "
                                       f"{role} added successfully!")

        # Clear the fields after adding the user
        user_name_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
        user_role_var.set("user")  # Reset to default role
    except sqlite3.IntegrityError:
        messagebox.showerror("Duplicate Error", "A person with this name already exists.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"A database error occurred: {e}")
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")


# Function to toggle password visibility
def toggle_password():
    if password_var.get():
        password_entry.config(show="")
    else:
        password_entry.config(show="*")


# Add User Frame (Admin Panel)
frame_add_user = tk.Frame(notebook)
notebook.add(frame_add_user, text="Add User")

# Add User Form
tk.Label(frame_add_user, text="Add New User", font=('Helvetica', 14)).pack(pady=(10, 5))

user_name_label = tk.Label(frame_add_user, text="Enter user's name", font=('Helvetica', 10))
user_name_label.pack(pady=(0, 5), padx=10)
user_name_entry = ttk.Entry(frame_add_user)
user_name_entry.pack(pady=(0, 5), padx=10, fill=tk.X)

password_label = tk.Label(frame_add_user, text="Enter user's password", font=('Helvetica', 10))
password_label.pack(pady=(0, 5), padx=10)
password_entry = ttk.Entry(frame_add_user, show="*")
password_entry.pack(pady=(0, 5), padx=10, fill=tk.X)

# Show Password Checkbox
password_var = tk.BooleanVar()
show_password_checkbox = tk.Checkbutton(frame_add_user, text="Show Password", variable=password_var,
                                        command=toggle_password)
show_password_checkbox.pack(pady=(0, 10), padx=10)

# User Role Dropdown
user_role_label = tk.Label(frame_add_user, text="Select user role", font=('Helvetica', 10))
user_role_label.pack(pady=(0, 5), padx=10)

role_options = ["Select Role", "user", "admin"]  # Role options
user_role_var = tk.StringVar()
user_role_var.set(role_options[0])  # Default value

user_role_dropdown = ttk.OptionMenu(frame_add_user, user_role_var, *role_options)
user_role_dropdown.pack(pady=(0, 5), padx=10, fill=tk.X)

# Add User Button
add_user_button = ttk.Button(frame_add_user, text="Add User", command=add_user)
add_user_button.pack(pady=(0, 10), padx=10, fill=tk.X)





def add_supplier():
    supplier_name = supplier_name_entry.get()
    contact_name = contact_name_entry.get()
    contact_email = contact_email_entry.get()
    contact_phone = contact_phone_entry.get()

    # Check if all fields are filled
    if not supplier_name or not contact_name or not contact_email or not contact_phone:
        messagebox.showwarning("Input Error", "All fields must be filled!")
        return

    # Validate email and phone
    if not is_valid_email(contact_email):
        messagebox.showwarning("Input Error", "Invalid email format!")
        return
    if not is_valid_phone(contact_phone):
        messagebox.showwarning("Input Error", "Phone number must be 10 digits!")
        return

    # Check if supplier already exists
    if is_supplier_exists(supplier_name, contact_email):
        messagebox.showwarning("Duplicate Entry", "Supplier already exists in the database!")
        return

    # Insert supplier into the database
    cursor.execute('''
        INSERT INTO suppliers (supplier_name, contact_name, contact_email, contact_phone)
        VALUES (?, ?, ?, ?)
    ''', (supplier_name, contact_name, contact_email, contact_phone))
    conn.commit()

    messagebox.showinfo("Success", "Supplier added successfully!")

    # Clear the input fields
    supplier_name_entry.delete(0, tk.END)
    contact_name_entry.delete(0, tk.END)
    contact_email_entry.delete(0, tk.END)
    contact_phone_entry.delete(0, tk.END)

    # Refresh the supplier list
    view_suppliers(frame_view_suppliers)


# Add Supplier Frame (Admin Panel)
frame_add_supplier = tk.Frame(notebook)
notebook.add(frame_add_supplier, text="Add Supplier")

# Add Supplier Form
tk.Label(frame_add_supplier, text="Add New Supplier", font=('Helvetica', 14)).pack(pady=(10, 5))

supplier_name_label = tk.Label(frame_add_supplier, text="Enter supplier name", font=('Helvetica', 10))
supplier_name_label.pack(pady=(0, 5), padx=10)
supplier_name_entry = ttk.Entry(frame_add_supplier)
supplier_name_entry.pack(pady=(0, 5), padx=10, fill=tk.X)

contact_name_label = tk.Label(frame_add_supplier, text="Enter contact name", font=('Helvetica', 10))
contact_name_label.pack(pady=(0, 5), padx=10)
contact_name_entry = ttk.Entry(frame_add_supplier)
contact_name_entry.pack(pady=(0, 5), padx=10, fill=tk.X)

contact_email_label = tk.Label(frame_add_supplier, text="Enter contact email", font=('Helvetica', 10))
contact_email_label.pack(pady=(0, 5), padx=10)
contact_email_entry = ttk.Entry(frame_add_supplier)
contact_email_entry.pack(pady=(0, 5), padx=10, fill=tk.X)

contact_phone_label = tk.Label(frame_add_supplier, text="Enter contact phone", font=('Helvetica', 10))
contact_phone_label.pack(pady=(0, 5), padx=10)
contact_phone_entry = ttk.Entry(frame_add_supplier)
contact_phone_entry.pack(pady=(0, 5), padx=10, fill=tk.X)

# Add Supplier Button
add_supplier_button = ttk.Button(frame_add_supplier, text="Add Supplier", command=add_supplier)
add_supplier_button.pack(pady=(10, 20), padx=10, fill=tk.X)


# View Suppliers Frame (Admin Panel)

def delete_supplier(tree):
    # Get the selected item
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Selection Error", "No supplier selected!")
        return

    # Get the supplier ID from the selected item
    supplier_name = tree.item(selected_item, "values")[0]

    # Confirm deletion
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete supplier name {supplier_name}?")
    if not confirm:
        return

    # Delete the supplier from the database
    cursor.execute("DELETE FROM suppliers WHERE supplier_name = ?", (supplier_name,))
    conn.commit()

    # Remove the selected item from the Treeview
    tree.delete(selected_item)

    # Success message
    messagebox.showinfo("Success", "Supplier deleted successfully!")


def view_suppliers(frame):
    # Clear the frame content to avoid duplicates
    for widget in frame.winfo_children():
        widget.destroy()

    # Title Label
    tk.Label(frame, text="List of Suppliers", font=("Arial", 16)).pack(pady=10)

    # Configure Treeview style to highlight selected row with blue background
    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.map(
        "Treeview",
        background=[("selected", "light blue")],
        foreground=[("selected", "white")]
    )

    # Create a Treeview widget for displaying suppliers in a table format
    tree = ttk.Treeview(frame, columns=("Supplier Name", "Contact Name", "Email", "Phone"), show="headings",
                        style="Treeview")
    tree.pack(pady=10, fill=tk.BOTH, expand=True)

    # Define the column headings
    # tree.heading("ID", text="ID")
    tree.heading("Supplier Name", text="Supplier Name")
    tree.heading("Contact Name", text="Contact Name")
    tree.heading("Email", text="Email")
    tree.heading("Phone", text="Phone")

    # Set the column widths
    # tree.column("ID", width=50, anchor=tk.CENTER)
    tree.column("Supplier Name", width=150)
    tree.column("Contact Name", width=120)
    tree.column("Email", width=150)
    tree.column("Phone", width=120)

    # Add scrollbar for better usability
    # scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    # tree.configure(yscroll=scrollbar.set)
    # scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Fetch all suppliers from the database
    cursor.execute('SELECT supplier_name , contact_name  ,contact_email ,contact_phone FROM suppliers')
    suppliers = cursor.fetchall()

    # Populate the Treeview with the supplier data
    for supplier in suppliers:
        tree.insert("", tk.END, values=(supplier[0], supplier[1], supplier[2], supplier[3]))

    # Add a Delete Supplier button
    delete_button = tk.Button(
        frame, text="Delete Supplier", command=lambda: delete_supplier(tree), bg="light grey", fg="black"
    )
    delete_button.pack(pady=10)

    # Ensure UI refresh
    frame.update_idletasks()


frame_view_suppliers = tk.Frame(notebook)
notebook.add(frame_view_suppliers, text="View Suppliers")

# View Suppliers Form
tk.Label(frame_view_suppliers, text="List of Suppliers", font=('Helvetica', 14)).pack(pady=(10, 5))

view_suppliers(frame_view_suppliers)

# Initialize

# create_tables()
update_location_dropdown()
view_locations()
fetch_items_view()
app.mainloop()