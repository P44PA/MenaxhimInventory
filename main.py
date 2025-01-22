import sqlite3
import tkinter as tk
from tkinter import messagebox
import subprocess  # To run external Python files
from Creator import *


# Database setup
conn = sqlite3.connect('school_inventory_gui.db')
cursor = conn.cursor()

create_all_tables()


def validate_login(username, password):
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    if user:
        return user[2]  # Return the role of the user (admin or user), which is at index 2
    return None

def log_user_activity(username, action):
    cursor.execute('''
        INSERT INTO user_activity_logs (username, action)
        VALUES (?, ?)
    ''', (username, action))
    conn.commit()

def login():
    def handle_login():
        username = username_entry.get()
        password = password_entry.get()
        role = validate_login(username, password)

        if role:
            # Log successful login
            log_user_activity(username, "Logged in successfully")
            messagebox.showinfo("Login Success", f"Welcome {username}!")
            login_window.destroy()  # Close the login window

            # Run the appropriate app based on the user's role
            if role == "admin":
                subprocess.run(["python", "AdminPage.py"])  # Run the admin app
            else:
                subprocess.run(["python", "RegularUser.py"])  # Run the user app
        else:
            # Log failed login attempt
            log_user_activity(username, "Failed login attempt")
            messagebox.showerror("Login Error", "Invalid username or password.")

    def toggle_password_visibility():
        if show_password_var.get():
            password_entry.config(show="")  # Show password
        else:
            password_entry.config(show="*")  # Hide password

    login_window = tk.Toplevel(app)
    login_window.title("Login - Sistemi Inventar Gjergj Canco")
    login_window.geometry("500x250")
    login_window.protocol("WM_DELETE_WINDOW", lambda: app.quit())

    tk.Label(login_window, text="Username:").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Password:").pack(pady=5)

    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    # Show Password Checkbox
    show_password_var = tk.BooleanVar()
    show_password_check = tk.Checkbutton(login_window, text="Show Password", variable=show_password_var,
                                         command=toggle_password_visibility)
    show_password_check.pack(pady=5)

    login_button = tk.Button(login_window, text="Login", command=handle_login)
    login_button.pack(pady=10)

    login_window.mainloop()

# Main Application Window
app = tk.Tk()

# Hide main window until login is successful
app.withdraw()  # Hide main window

# Open login window
login()

app.mainloop()



