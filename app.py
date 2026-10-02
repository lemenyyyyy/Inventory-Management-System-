from dotenv import load_dotenv

load_dotenv()
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 19 19:37:33 2025

@author: PRASAD RANSUBHE
"""

import pandas as pd
import datetime as dt
import mysql.connector
import os
import matplotlib.pyplot as plt
import sys

# ======================================================================
# 2. MySQL connection Configuration
# ======================================================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "chocolate_shop"),
}

INVENTORY_FILE = 'inventory.txt'
INVENTORY_SIZE = 28
DEFAULT_STOCK = 100

#--- Helper Functions (Database & Security)
def connect_to_database_safe():
    """Connects to MySQL database. This is the only permitted place for try/except due to external resource dependency."""
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        return db
    except mysql.connector.Error as err:
        print(f"\n[!!! Database Error !!!] Error connecting: {err}")
        print("Please ensure MySQL is running and credentials are correct.")
        return None

def setup_database():
    """Sets up the required tables, including the new 'feedback' table with manager_reply column."""
    print("Initializing database...")
    db = connect_to_database_safe()
    if db is not None:
        cursor = db.cursor()
        
        # 1. Customers Table (Using AUTO_INCREMENT to prevent primary key errors)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255),
            mobile VARCHAR(15) UNIQUE,
            username VARCHAR(255) UNIQUE,
            password VARCHAR(255)
        )
        """)
        
        # 2. Managers Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS managers (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(255) UNIQUE,
            password VARCHAR(255)
        )
        """)
        
        # 3. Sales Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INT PRIMARY KEY AUTO_INCREMENT,
            timestamp DATETIME,
            product_name VARCHAR(255),
            quantity INT,
            unit_price DECIMAL(10, 2),
            total DECIMAL(10, 2)
        )
        """)
        
        # 4. Feedback Table (Includes timestamp and manager_reply)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INT PRIMARY KEY AUTO_INCREMENT,
            customer_id INT,
            product_name VARCHAR(255),
            rating INT,
            comment TEXT,
            timestamp DATETIME,
            manager_rel VARCHAR(50), 
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
        """)
        
        db.commit()
        cursor.close()
        db.close()
        print("Database setup complete.")
    else:
        print("Database setup failed due to connection error.")

def log_transaction_to_db(product_name, quantity, unit_price, transaction_time=None):
    """Logs sales to the database."""
    db = connect_to_database_safe()
    if db is None:
        return False
    
    if transaction_time is None:
        transaction_time = dt.datetime.now()
    formatted_time = transaction_time.strftime('%Y-%m-%d %H:%M:%S')
    
    total_sale = quantity * unit_price
    
    py_quantity = int(quantity)
    py_unit_price = float(unit_price)
    py_total_sale = float(total_sale)
    
    cursor = db.cursor()
    query = """INSERT INTO sales (timestamp, product_name, quantity, unit_price, total) VALUES (%s, %s, %s, %s, %s)"""
    
    cursor.execute(query, (formatted_time, product_name, py_quantity, py_unit_price, py_total_sale))
    db.commit()
    cursor.close()
    db.close()
    return True

# --- Helper Functions (Persistent Data - Inventory)
def load_inventory():
    """Loads inventory from file, initializing if necessary."""
    if not os.path.exists(INVENTORY_FILE):
        default_data = ','.join([str(DEFAULT_STOCK)] * INVENTORY_SIZE)
        with open(INVENTORY_FILE, 'w') as f:
            f.write(default_data)
            
    with open(INVENTORY_FILE, 'r') as f:
        data=f.read().split(',')
    inventory =[]
    for d in data:
        d_stripped = d.strip()
        if len(d_stripped) > 0 and (d_stripped.isdigit() or (d_stripped.startswith('-') and d_stripped[1:].isdigit())):
            inventory.append(int(d_stripped))
        else:
            inventory.append(DEFAULT_STOCK) 
            
    if len(inventory) < INVENTORY_SIZE:
        i=0
        for _ in range(INVENTORY_SIZE - len(inventory)):
            inventory.append(DEFAULT_STOCK)
            i=i+1 
            
    return inventory[:INVENTORY_SIZE]

def save_inventory(data):
    """Saves inventory data to file."""
    with open(INVENTORY_FILE, 'w') as f:
        f.write(','.join(map(str, data)))

# --- Product & Price Definitions
def get_product_data():
    """Returns product dataframes with up-to-date stock."""
    inventory = load_inventory()
    
    chocolates = pd.DataFrame({
        'Name': ['Cocoa Pure Chocolate', 'Sea Salt Chocolate', 'Orange and Almond Chocolate', 
                 'Rasberry and Hazelnut Chocolate', 'Milk Chocolate', 'Caramel Chocolate', 
                 'White Chocolate', 'Coconut Intense Chocolate', 'Cranberry Hazelnut Chocolate',
                 'Honeycomb Chocolate', 'Mint Chocolate'],
        'Price': [799, 795, 799, 799, 225, 599, 399, 399, 499, 399, 499],
        'Stock': inventory[0:11]
    })
    
    pralines = pd.DataFrame({
        'Name': ['Milk Praline', 'White Praline', 'Dark Praline', 
                 'Almond Praline', 'Caramel Praline', 'Coconut Praline', 
                 'Coffee Praline', 'Hazelnut Praline', 'Strawberries Praline',
                 'Orange Praline', 'Mint Praline'],
        'Price': [579, 579, 579, 745, 745, 735, 839, 735, 835, 835, 579],
        'Stock': inventory [11:22]
    })
    
    cakes = pd.DataFrame({
        'Name': ['Chocolate Cake', 'Tiramisu', 'Brownie', 'Creme Brulee', 'Millefeuille', 'Lemon Meringue'],
        'Price': [899, 899, 899, 899, 899, 899],
        'Stock': inventory[22:28]
    })
    
    return chocolates, pralines, cakes

def get_all_product_names_and_prices():
    """Returns a dictionary of all products and their prices."""
    chocolates, pralines, cakes = get_product_data()
    all_products = pd.concat([chocolates, pralines, cakes], ignore_index=True)
    return dict(zip(all_products['Name'], all_products['Price']))

#--- Console UI Helpers ---
def get_int_input(prompt, min_val=None, max_val=None):
    """Safely gets integer input using if/else checks (no try/except)."""
    user_input = input(prompt)
    is_valid = user_input.isdigit() 
    
    if user_input.startswith('-') and user_input[1:].isdigit():
        is_valid = True
        
    if is_valid:
        value = int(user_input)
        
        if min_val is not None and value < min_val:
            print(f"Input must be greater than or equal to {min_val}.")
            return None
        if max_val is not None and value > max_val:
            print(f"Input must be less than or equal to {max_val}.")
            return None
        return value
    else:
        print("Invalid input. Please enter a whole number.")
        return None

def get_float_input(prompt):
    """Safely gets float input using if/else checks (no try/except)."""
    user_input = input(prompt)
    is_float = False
    
    dot_count = 0
    clean_input = user_input
    if user_input.startswith('-'):
        clean_input = user_input[1:]
        
    # Count dots
    i=0
    for char in clean_input:
        if char == '.':
            dot_count = dot_count + 1
        i=i+1
        
    if len(user_input) > 0 and dot_count <= 1:
        parts = clean_input.split('.')
        all_parts_are_digits = True
        for part in parts:
            if not part.isdigit():
                all_parts_are_digits = False
        if all_parts_are_digits:
            is_float = True
            
    if is_float:
        return float(user_input)
    else:
        print("Invalid input. Please enter a valid number (e.g., 100 or 100.50).")
        return None

# ======================================================================
# 4. Login Portal Functions
# ======================================================================
def login_user(username, password, user_type):

    db = connect_to_database_safe()
    if db is None:
        return None
    
    cursor = db.cursor()
    # Fetch all relevant columns
    if user_type == 'customers':
        query = "SELECT id, name, mobile, username, password FROM customers WHERE username = %s AND password = %s"
    else:
        query = "SELECT id, username, password FROM managers WHERE username = %s AND password = %s"

    cursor.execute(query, (username, password))
    user_data = cursor.fetchone()
    cursor.close()
    db.close()
    return user_data

def handle_login(user_type):
    """Handles the CLI login process."""
    print(f"\n--- {user_type.title()} Login ---")
    username = input("Enter Username: ")
    password = input("Enter Password: ")
    
    if (not username) or (not password):
        print("Login Failed: Username and password cannot be empty.")
        return None
        
    user = login_user(username, password, user_type)
    
    if user:
        print(f"Success! Logged in as {username}.")
        if user_type == 'customers':
            # user tuple: (id, name, mobile, username, password)
            return {'id': user[0], 'name': user[1], 'mobile': user[2], 'role': 'customer'}
        else: # managers (id, username, password)
            return {'id': user[0], 'username': user[1], 'role': 'manager'}
    else:
        print("Login Failed: Invalid username or password.")
        return None

def handle_registration():
    """Handles the CLI customer registration process using pre-checks."""
    print("\n--- New Customer Registration ---")
    name = input("Enter your full name: ")
    mobile = input("Enter your 10-digit mobile number: ")
    username = input("Choose a username (e.g., name@123): ")
    password = input("Choose a password: ")
    
    if (len(mobile) != 10) or (not mobile.isdigit()):
        print("Error: Invalid mobile number. Please enter 10 digits.")
        return
        
    db= connect_to_database_safe()
    if db is None:
        return
        
    cursor = db.cursor() 
    
    # Conditional Check 1: Mobile exists?
    cursor.execute("SELECT 1 FROM customers WHERE mobile = %s", (mobile,)) 
    if cursor.fetchone(): 
        print("Error: Mobile number already exists.") 
        cursor.close() 
        db.close() 
        return 
    
    # Conditional Check 2: Username exists?
    cursor.execute("SELECT 1 FROM customers WHERE username = %s", (username,)) 
    if cursor.fetchone(): 
        print("Error: Username already exists.") 
        cursor.close() 
        db.close() 
        return 
        
    query = "INSERT INTO customers (name, mobile, username, password) VALUES (%s, %s, %s, %s)" 
    
    cursor.execute(query, (name, mobile, username,password)) 
    db.commit() 
    print("Success! Registration successful. You can now log in.") 
    
    cursor.close() 
    db.close()

def handle_forgot_password(): 
    """Handles the CLI password reset process for customers.""" 
    print("\n--- Forgot Password ---") 
    username = input("Enter your username: ") 
    mobile = input("Enter your registered mobile number: ") 
    
    db = connect_to_database_safe() 
    if db is None: 
        return 
    
    cursor = db.cursor() 
    cursor.execute("SELECT * FROM customers WHERE username = %s AND mobile = %s", (username, mobile)) 
    
    if cursor.fetchone(): 
        new_password = input("Enter your new password: ") 
        if len(new_password) > 0: 
            password =new_password 
            cursor.execute("UPDATE customers SET password = %s WHERE username = %s", (password, username)) 
            
            db.commit() 
            print("Success! Password has been reset successfully.") 
        else: 
            print("Error: New password cannot be empty.") 
    else: 
        print("Error: Username and mobile number do not match our records.") 
        
    cursor.close() 
    db.close()

def view_public_feedback():
    """
    Displays customer feedback and manager replies for public viewing (Auth Portal),
    allowing filtering by product.
    """
    print("\n--- Public Customer Feedback & Manager Replies ---")
    db = connect_to_database_safe()
    if db is None:
        return

    cursor = db.cursor(dictionary=True)
    
    # 1. Get list of all products that have feedback
    cursor.execute("SELECT DISTINCT product_name FROM feedback ORDER BY product_name ASC")
    product_names = [d['product_name'] for d in cursor.fetchall()]
    
    if not product_names:
        print("No customer feedback has been submitted yet.")
        cursor.close()
        db.close()
        return

    # 2. Present selection menu
    print("\nSelect an option to view feedback:")
    print(" [0] View ALL Products")
    products_map = {i + 1: name for i, name in enumerate(product_names)}
    for key, name in products_map.items():
        print(f" [{key}] {name}")
    print("-" * 40)
    
    max_index = len(products_map)
    selected_product = None
    
    selection_running = True
    for _ in range(100000): # Loop to handle product selection
        if not selection_running:
            break
            
        choice_input = input(f"Enter choice (0-{max_index}) or 'exit' to return: ").strip().lower()
        
        if choice_input == 'exit':
            cursor.close()
            db.close()
            return
            
        try:
            choice = int(choice_input)
            if 0 <= choice <= max_index:
                if choice > 0:
                    selected_product = products_map[choice]
                selection_running = False
            else:
                print(f"Invalid choice. Please enter a number between 0 and {max_index} or 'exit'.")
        except ValueError:
            print("Invalid input. Please enter a number or 'exit'.")

    # 3. Construct SQL query with filtering
    query = """
    SELECT f.product_name, f.rating, f.comment, f.manager_rel, f.timestamp 
    FROM feedback f 
    """
    params = []
    
    if selected_product:
        query += " WHERE f.product_name = %s"
        params.append(selected_product)
        display_title = selected_product
    else:
        display_title = "ALL Products"
    
    query += " ORDER BY f.timestamp ASC"

    cursor.execute(query, tuple(params))
    feedback_records = cursor.fetchall()
    cursor.close()
    db.close()
    
    if not feedback_records:
        print(f"No feedback found for {display_title}.")
        return

    # 4. Display the results
    df = pd.DataFrame(feedback_records)
    
    print(f"\n--- Showing Feedback for: {display_title} (Newest at Bottom) ---")
    
    # Define widths for columns based on selection
    if selected_product:
        # Filtered view: Product name is implicit, so make Comment/Reply wider
        comment_width, reply_width, total_width = 45, 45, 120
        header_format = f"{'Timestamp':<20} {'Rating':<10} {'Customer Comment':<{comment_width}} {'Manager Reply':<{reply_width}}"
        row_format = f"{{:<20}} {{:<10}} {{:<{comment_width}}} {{:<{reply_width}}}"
    else:
        # All products view: Use standard widths
        comment_width, reply_width, total_width = 40, 40, 145
        header_format = f"{'Timestamp':<20} {'Product':<30} {'Rating':<10} {'Customer Comment':<{comment_width}} {'Manager Reply':<{reply_width}}"
        row_format = f"{{:<20}} {{:<30}} {{:<10}} {{:<{comment_width}}} {{:<{reply_width}}}"
    
    print(header_format)
    print("-" * total_width)
    
    for _, row in df.iterrows():
        comment_text = row['comment'] if row['comment'] else ""
        reply_text = row['manager_rel'] if row['manager_rel'] else "No reply yet"
        
        # Truncate and add ellipsis for display
        comment_excerpt = comment_text[:comment_width-3] + '...' if len(comment_text) > comment_width else comment_text
        reply_excerpt = reply_text[:reply_width-3] + '...' if len(reply_text) > reply_width else reply_text
        
        
        if selected_product:
            print(row_format.format(
                row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 
                row['rating'], 
                comment_excerpt, 
                reply_excerpt))
        else:
            print(row_format.format(
                row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                row['product_name'],
                row['rating'],
                comment_excerpt,
                reply_excerpt))

    print("-" * total_width)


def auth_portal(): 
    """The main authentication/login menu, uses for loop instead of while.""" 
    user = None 
    
    portal_running = True
    for _ in range(100000): 
        if not portal_running:
            return
            
        print("\n" + "="*50) 
        print("🍫🍫 Welcome to Chocolate Apocalypse🍫 🍫 ".center(50)) 
        print("="*50) 
        print("1. Customer Login") 
        print("2. Manager Login") 
        print("3. New Customer Registration") 
        print("4. Forgot Password (Customer)") 
        print("5. View Latest Feedback (Public)")
        print("6. About Us") 
        print("7. Exit Application") 
        
        print("-" * 50) 
        
        choice = input("Enter choice (1-7): ") 
        
        if choice == '1': 
            user = handle_login('customers') 
            if user: 
                portal_running = False
                return user 
        
        elif choice == '2': 
            user = handle_login('managers') 
            if user: 
                portal_running = False
                return user 
        
        elif choice == '3': 
            handle_registration()
        
        elif choice == '4': 
            handle_forgot_password() 
        
        elif choice == '5': 
            view_public_feedback() # New Option
        
        elif choice == '6': 
            print("Welcome to Chocolate Apocalypse, where the world ending is just an excuse for another exquisite bite! Born from a passion for the darkest cocoa and a disregard for diets, we believe that if the asteroids are falling, you might as well go out with a mouthful of heaven.") 
            print("Our shop is a bunker of bliss, a sanctuary stocked with truffles that explode with flavor, bars so rich they're practically a sin, and hot chocolate thick enough to stir with a wrench. We source fair-trade cocoa from around the globe, hand-crafting unique, often bizarre, confections that promise a delicious escape from the mundane.") 
            print("Stop by. Prepare your taste buds for the inevitable, glorious sugary doom. We promise you won't survive the experience... without ordering more.") 
        
        elif choice == '7': 
            print("Exiting Chocolate Apocalypse. Goodbye!") 
            sys.exit(0) 
        
        else: 
            print("Invalid choice. Please enter a number between 1 and 7.")

# ======================================================================
# 5. Customer Portal Functions
# ======================================================================
def display_products_for_category(category_df, offset, category_name): 
    products_with_index = [] 
    print(f"\n--- {category_name.title()} Menu ---") 
    print(f"{'Index':<7} {'Name':<35} {'Price (Rs.)':<15} {'Stock':<10}")
    print("-" * 67) 
    
    for index, row in category_df.iterrows(): 
        global_index = offset + index 
        if row['Stock'] > 0:
            print(f"{global_index:<7} {row['Name']:<35} {row['Price']:<15.2f} {row['Stock']:<10}")
            products_with_index.append({
                'index': global_index, 
                'name': row['Name'], 
                'price': row['Price'], 
                'stock': row['Stock']
            })
    
    print("-" * 67)
    return products_with_index

def handle_category_shopping(category_name, offset, current_order):
    chocolates, pralines, cakes = get_product_data()
    df = None
    if category_name == 'Chocolates':
        df = chocolates
    elif category_name == 'Pralines':
        df = pralines
    elif category_name == 'Cakes':
        df = cakes

    if df is None:
        return

    products_list = display_products_for_category(df, offset, category_name)
    max_index = offset + len(df) - 1
    
    menu_running = True
    for _ in range(100000):
        if not menu_running:
            return
            
        index_input = input(f"Enter product index ({offset} to {max_index}) to add to cart, or type 'done' to return to main menu: ").strip().lower()

        if index_input == 'done':
            menu_running = False
            return

        try:
            product_index = int(index_input)
            if not (offset <= product_index <= max_index):
                print(f"Invalid input. Index must be between {offset} and {max_index}.")
                continue
        except ValueError:
            print("Invalid input. Please enter a whole number index or 'done'.")
            continue

        selected_product = None
        for p in products_list:
            if p['index'] == product_index:
                selected_product = p
                break
            
            print("Invalid product index selected.")
            continue
            
        print(f"Selected: {selected_product['name']} (Stock: {selected_product['stock']})")
        
        # Check stock before proceeding
        if selected_product['stock'] <= 0:
            print("Sorry, this item is out of stock.")
            continue
            
        quantity = get_int_input("Enter Quantity: ", min_val=1, max_val=selected_product['stock'])
        
        if quantity is None:
            continue
            
        # 1. Add item to cart list
        current_order.append({
            'index': product_index,  
            'name': selected_product['name'],
            'price': selected_product['price'],
            'quantity': quantity
        })
        print(f"Added {quantity} x {selected_product['name']} to cart.")
        
        idx = product_index
        
        inventory = load_inventory()
        
        if 0 <= idx < len(inventory):
            inventory[idx] = inventory[idx] - quantity
            save_inventory(inventory)
            print(f"Stock committed for {selected_product['name']}. Current stock: {inventory[idx]}.")
        else:
            print(f"Internal error: Cannot update inventory index {idx}.")
            
    

def update_inventory_and_log_sale(order_item, all_product_data):
    inventory = load_inventory()
    
    idx = order_item['index']
    qty_purchased = order_item['quantity']
    product_name = order_item['name']
    unit_price = order_item['price']
    
    if 0 <= idx < len(inventory):
        inventory[idx] = inventory[idx] - qty_purchased
        save_inventory(inventory)
        
        log_transaction_to_db(product_name, qty_purchased, unit_price)
        return True
    else:
        print(f"Internal error: Cannot update inventory index {idx}.")
        return False

def handle_customer_feedback(user):
    print("\n--- Submit Product Feedback ---")
    chocolates, pralines, cakes = get_product_data()
    all_products = pd.concat([chocolates, pralines, cakes], ignore_index=True)
    print("\nAvailable Products for Feedback:")
    products_list = all_products['Name'].tolist()
    i = 0
    for name in products_list:
        print(f" [{i + 1}] {name}")
        i = i + 1
    print("-" * 50)
    print("To exit without submitting feedback, enter 0.")

    feedback_running = True
    for _ in range(100000):
        if not feedback_running:
            return
            
        max_index = len(products_list)
        product_index_input = get_int_input(f"Enter the product number (1-{max_index}) or 0 to exit: ", min_val=0, max_val=max_index)
        
        if product_index_input is None:
            continue
        
        if product_index_input == 0:
            print("Exiting feedback submission.")
            feedback_running = False
            return

        selected_index = product_index_input - 1
        # Defensive check
        if selected_index < 0 or selected_index >= len(products_list):
            print("Invalid product selection index.")
            continue
            
        product_name = products_list[selected_index]
        print(f"\n--- Feedback for: {product_name} ---")

        rating = get_int_input("Enter Rating (1-5): ", min_val=1, max_val=5)
        if rating is None:
            continue

        comment = input("Enter Feedback Comment (under 300 words, or '.' to skip): ")
        
        if comment == '.':
            comment = ""
        
        # Simple word count check
        if len(comment.split()) > 300:
            print("Error: Comment must be under 300 words.")
            continue

        db = connect_to_database_safe()
        if db is None:
            continue

        cursor = db.cursor()
        transaction_time = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
        query = "INSERT INTO feedback (customer_id, product_name, rating, comment, timestamp) VALUES (%s, %s, %s, %s, %s)"
        
        cursor.execute(query, (user['id'], product_name, rating, comment, transaction_time))
        db.commit()
        print("\nSuccess! Your feedback has been recorded.")
        cursor.close()
        db.close()
        feedback_running = False
        return 


def handle_checkout(user, current_order):
    """Processes the checkout, updates inventory, and logs sales."""
    if not current_order:
        print("\n[!] Your cart is empty. Nothing to checkout.")
        return
    
    transaction_time = dt.datetime.now()
    display_time = transaction_time.strftime('%Y-%m-%d %I:%M:%S %p')
        
 
    print("\n" + "="*60)
    print("CHECKOUT INVOICE".center(60))
    print("="*60)
    print(f"Customer: {user['name']}")
    print(f"Date/Time: {display_time}")
    print("-" * 60)
    print(f"{'Item':<35} {'quantity':<5} {'Price':<10} {'Total':<10}")
    print("-" * 60)
    
    grand_total = 0
    
    for item in current_order:
        total = item['quantity'] * item['price']
        sub_total = grand_total + total
        grand_total=sub_total*1.05
    
        print(f"{item['name']:<35} {item['quantity']:<5} {item['price']:<10.2f} {total:<10.2f}")
        
        log_transaction_to_db(item['name'], item['quantity'], item['price'], transaction_time)
        
    print("-" * 60)
    print("CGST INCLUDED=.25%")
    print("SGST INCLUDED=.25%")
    print(f"{'GRAND TOTAL:':<50} {grand_total:<10.2f}")
    
    print("="*60)
    print("-" * 60)
    print("\n--- Select Payment Method ---")
    print("1. Cash (Pay on Delivery/Pickup)")
    print("2. Card (Debit/Credit)")
    print("3. UPI")
    print("-" * 60)
   
    payment_choice = get_int_input("Select Payment Method (1-3): ", min_val=1, max_val=3)
   
    payment_method = "UNKNOWN"
   
    if payment_choice == 1:
       payment_method = "Cash"
       print("\n[i] Payment selected: Cash. Please pay the amount upon delivery/pickup.")
       print("Goodbye!")
       
    elif payment_choice == 2:
        payment_method = "Card"
        print("\n[i] Payment selected: Card")
        
        try:
            a = input("Enter Card type (credit or debit): ")
            b = input("Enter Card number (16 digits): ")
        
            if not b.isdigit() or len(b) != 16:
                print("Error: Card number must be 16 numeric digits. Payment failed. ❌")
                return
                
            c = int(input("Enter CSV (3 digits): "))

            if 1 <= c <= 999:
            
                print(f"Payment received of: Rs. {grand_total:.2f}")
                print("-" * 60)
                print(f"Payment Confirmed, received of: Rs. {grand_total:.2f} ✅")
                print("Goodbye! 👋")
            else:
                print("Error: Incorrect CSV. It must be a 3-digit number (1-999). Payment failed. ❌")
                
        except ValueError:
            print("Error: Invalid input for Card number or CSV. Please enter only numbers. Payment failed. ❌")

           
    if payment_choice == 3:
           payment_method = "UPI"
           upi_id = "chocolate.apocalypse@upi"
           url = "8266378917"
           print("\n[i] Payment selected: UPI.")
           print("-" * 30)
           print(f"UPI ID: {upi_id}")
           print(f"Total Amount Due: Rs. {grand_total:.2f}")
           
           print("************************************************************")
           print("Kindly note the number for qr scanning:")
           print("DATA",upi_id,url)
           print("************************************************************")
    return

    print("THANK YOU FOR PURCHASE!!!")
    print("\n[i] Sales Log Updated.")

def customer_portal(user): 
    """The main customer interaction loop, uses for loop instead of while.""" 
    current_order = [] 
    
    portal_running = True
    for _ in range(100000): 
        if not portal_running:
            return
            
        print("\n" + "="*50) 
        print(f"Welcome, {user['name']}! (Customer Portal)") 
        print("="*50) 
        print("1. View Chocolates Menu") 
        print("2. View Pralines Menu") 
        print("3. View Cakes Menu") 
        print("4. View Cart & Checkout") 
        print("5. Submit Product Feedback")
        print("6. Logout")
        print("-" * 50) 
        
        choice = input("Enter choice (1-6): ")
        
        if choice == '6':
            print("Logging out.") 
            portal_running = False
            return 
        
        elif choice == '1': 
            handle_category_shopping('Chocolates', 0, current_order) 
            
        elif choice == '2': 
            handle_category_shopping('Pralines', 11, current_order) 
            
        elif choice == '3': 
            handle_category_shopping('Cakes', 22, current_order) 
            
        elif choice == '4': 
            handle_checkout(user, current_order) 
            current_order = [] 
            
        elif choice == '5':
            handle_customer_feedback(user)
            
        else: 
            print("Invalid choice. Please enter a number between 1 and 6.")

# ======================================================================
# 6. Manager Portal Functions
# ======================================================================
def open_sales_report():
    print("\n--- Annual Product Sales Report Generator ---")
    
    # 1. Database Connection for fetching product list
    db = connect_to_database_safe()
    if db is None:
        return
    cursor = db.cursor()
    
    # Fetch all unique product names from the sales table
    cursor.execute("SELECT DISTINCT product_name FROM sales ORDER BY product_name ASC")
    product_records = cursor.fetchall()
    
    if len(product_records) == 0:
        print("Error: No products found in the sales history.")
        cursor.close()
        db.close()
        return

    # Create a list of product names and display them
    available_products = [record[0] for record in product_records]
    print("\nAvailable Products:")
    for i, name in enumerate(available_products):
        print(f"  [{i + 1}] {name}")
    print("-" * 30)

    # 2. 
    # Input: Prompt for the year
    year = get_int_input("Enter year for annual report (avail report from 2022 jan): ", min_val=2020, max_val=2100)
    if year is None:
        cursor.close()
        db.close()
        return
    
    # 2. Input: Prompt for the product INDEX number
    max_index = len(available_products)
    product_index_input = get_int_input(f"Enter the product number (1-{max_index}) to plot: ", min_val=1, max_val=max_index)
    if product_index_input is None:
     
        cursor.close()
        db.close()
        return
    

    selected_index = product_index_input - 1
    product_name = available_products[selected_index]

    cursor.close() 
    cursor = db.cursor(dictionary=True) 

    query = """
   
        SELECT timestamp, total
        FROM sales
        WHERE YEAR(timestamp) = %s AND product_name = %s
        ORDER BY timestamp ASC
    """

    cursor.execute(query, (year, product_name)) 
    sales_records = cursor.fetchall()
    cursor.close()
    db.close() 
    
    if len(sales_records) == 0:
     

        print(f"No sales data found for '{product_name}' in the year {year}.")
        return
        
    df = pd.DataFrame(sales_records)
    
    df['total'] = pd.to_numeric(df['total']) 
    df['Timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 3. Grouping: Group sales by MONTH for an annual trend report
    monthly_sales = df.groupby(df['Timestamp'].dt.to_period('M'))['total'].sum()
    
    # Convert PeriodIndex to string for clear x-axis labels (e.g., "2024-01")
    monthly_sales.index = monthly_sales.index.astype(str)
    
    # 4. Plotting
    
    plt.figure(figsize=(12, 6))
    
    # Plot the monthly trend
    monthly_sales.plot(kind='line',marker='o',linestyle='-',color='blue',linewidth=2)
    
    # Update title to reflect the specific product report
    plt.title(f"Monthly Sales Trend for: {product_name} ({year})", fontsize=16, color='black')
    plt.xlabel("Month (Year-Month)")
    plt.ylabel("Total Sales")
    plt.grid(axis='y', linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    print(f"\n[i] Generating and displaying Monthly Sales Trend Plot for {product_name} in {year}...")
    plt.show()

def handle_inventory_update():
    
    # Display current inventory
    print("\n--- Current Inventory ---")
    chocolates, pralines, cakes = get_product_data()
    all_products = pd.concat([chocolates, pralines, cakes], ignore_index=True)
    
    print(f"{'Index':<7} {'Name':<35} {'Price (Rs.)':<15} {'Stock':<10}")
   
    print("-" * 67)
    
    for index, row in all_products.iterrows():
        print(f"{index:<7} {row['Name']:<35} {row['Price']:<15.2f} {row['Stock']:<10}")
        
    print("\nUse Item Index (0-27) to update stock.")
    
    # Get index
    index = get_int_input(f"Enter Item Index (0 to {INVENTORY_SIZE-1}, or -1 to cancel): ", min_val=-1, max_val=INVENTORY_SIZE-1)
    if (index is None) or (index == -1):
        return
        
 
    # Get stock change
    quantity_change = get_int_input("Enter Stock Change (+ or - number): ")
    if quantity_change is None:
        return
        
    inventory = load_inventory()
    
    new_stock = inventory[index] + quantity_change
    
    if new_stock < 0:
        print(f"Inventory Error: Stock cannot go below zero.Current stock is {inventory[index]}.")
        return
        
    # Update logic
    inventory[index] = new_stock
    save_inventory(inventory)
    
    print(f"\nSuccess! Stock for index {index} updated to {new_stock}.")
    
def open_customers_view():
    """Displays a list 
 of all registered customers."""
    print("\n--- Registered Customers ---")
    db = connect_to_database_safe()
    if db is None:
        return
    
    cursor = db.cursor()
    cursor.execute("SELECT name, mobile, username FROM customers ORDER BY name")
    customers = cursor.fetchall()
    cursor.close()
    db.close()
    
    if len(customers) == 0:
        print("No customers registered yet.")
        return
   
      
    print(f"{'Name':<30} {'Mobile':<15} {'Username':<30}")
    print("-" * 75)
    
    for customer in customers:
        print(f"{customer[0]:<30} {customer[1]:<15} {customer[2]:<30}")

def handle_add_manager():
    print("\n--- Add New Manager ---")
    db = connect_to_database_safe()
    if db is None:
        return
        
    username = input("Enter new Manager Username: ")
    password = input("Enter new Manager Password: ")
    
    if (not username) or (not password):
        print("Error: Username and password cannot be empty.")
        db.close()
        return
        
    cursor = db.cursor()
    cursor.execute("SELECT 1 FROM managers WHERE username = %s", (username,))
    if cursor.fetchone():
        print("Error: Manager username already exists.")
        cursor.close()
        db.close()
        return
        
    query = "INSERT INTO managers (username, password) VALUES (%s, %s)"
    cursor.execute(query, (username, password))
    db.commit()
    print(f"Success! Manager '{username}' added.")
    
    cursor.close()
    db.close()

def handle_manual_sale():
    print("\n--- Manually Log Sale ---")
    all_products = get_all_product_names_and_prices()
    
    print("Available products:")
    i = 0
    for name in all_products:
        print(f" [{i}] {name}")
        i = i + 1
    
    product_name = input("Enter Product Name (must match exactly): ")
    
    unit_price = all_products.get(product_name)
    
    if unit_price is None:
        print("Error: Product name not found in inventory.")
        return
        
    quantity = get_int_input("Enter Quantity Sold: ", min_val=1)
    if quantity is None:
        return
    if log_transaction_to_db(product_name, quantity, unit_price):
        print(f"\nSuccess! Sale for {product_name} x{quantity} logged successfully with the current system time.")
    else:
        print("\nFailed to log sale due to a database error.")
        
def handle_feedback_reply(db, product_names, get_int_input, input):
    """Handles the manager's action to reply to a specific feedback."""
    print("\n--- Reply to Customer Feedback ---")
    
    # 1. List products with feedback
    print("Products with Feedback:")
    products_with_feedback = {i + 1: name for i, name in enumerate(product_names)}
    i = 0
    for key, name in products_with_feedback.items():
        print(f" [{key}] {name}")
        i = i + 1
    print("-" * 40)
    
    max_index = len(products_with_feedback)
    product_choice = None
    
    selection_running = True
    for _ in range(100000): # Product selection loop
        if not selection_running:
            return
            
        product_choice_input = get_int_input(f"Enter product number (1-{max_index}) to view reviews for reply, or 0 to exit: ", min_val=0, max_val=max_index)
        
        if product_choice_input == 0:
            selection_running = False
            return
            
        if product_choice_input in products_with_feedback:
            product_choice = product_choice_input
            break
        else:
            print("Invalid choice.")
            
    if product_choice is None: 
        return
        
    selected_product = products_with_feedback[product_choice]
    
    cursor = db.cursor(dictionary=True)
    # Fetch feedback for the selected product, ordered ASC (newest at bottom)
    query = """
    SELECT f.id, f.product_name, f.rating, f.comment, c.username, f.timestamp, f.manager_rel
    FROM feedback f JOIN customers c ON f.customer_id = c.id 
    WHERE f.product_name = %s
    ORDER BY f.timestamp ASC
    """
    cursor.execute(query, (selected_product,))
    
    reviews_to_reply = cursor.fetchall()
    
    if not reviews_to_reply:
        print(f"No feedback found for {selected_product}.")
        cursor.close()
        return

    # Display reviews with index for reply
    print(f"\nReviews for {selected_product} (Newest at Bottom):")
    
    i = 0
    for review in reviews_to_reply:
        i += 1
        print("-" * 50)
        print(f" [Index: {i}] | ID: {review['id']} | Rating: {review['rating']} | Time: {review['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Customer ({review['username']}): {review['comment']}")
        print(f"Manager Reply: {review['manager_rel'] if review['manager_rel'] else 'No reply yet'}")
        review['display_index'] = i # Add temporary display index

    print("-" * 50)
    
    reply_index = None
    reply_running = True
    for _ in range(100000): # Reply selection loop
        if not reply_running:
            cursor.close()
            return

        index_input = get_int_input(f"Enter review index (1-{len(reviews_to_reply)}) to reply/edit, or 0 to exit: ", min_val=0, max_val=len(reviews_to_reply))
        
        if index_input == 0:
            reply_running = False
            cursor.close()
            return
        
        if index_input:
            reply_index = index_input
            break 

    
    selected_review = None
    for review in reviews_to_reply:
        if review['display_index'] == reply_index:
            selected_review = review
            break

    if selected_review is None:
        print("Invalid review index.")
        cursor.close()
        return
        
    print(f"\nSelected review by {selected_review['username']}: {selected_review['comment']}")
    new_reply = input("Enter your new reply (or leave empty to keep existing reply): ")
    
    if len(new_reply.split()) > 300:
        print("Error: Reply must be under 300 words.")
        cursor.close()
        return

    if new_reply:
        cursor.execute("UPDATE feedback SET manager_rel = %s WHERE id = %s", (new_reply, selected_review['id']))
        db.commit()
        print(f"Success! Reply to review ID {selected_review['id']} updated.")
    else:
        print("No change made to the reply.")
        
    cursor.close()
    return

def display_feedback_reviews(db, product_names, get_int_input):
    """
    Displays customer comments and manager replies, filtered by product if selected (restored original logic).
    """
    print("\n--- View Customer Reviews & Manager Replies ---")
    
    # 1. Ask manager for product selection
    print(" [0] View ALL Products")
    products_with_feedback = {i + 1: name for i, name in enumerate(product_names)}
    
    i = 0
    for key, name in products_with_feedback.items():
        print(f" [{key}] {name}")
        i = i + 1
    print("-" * 40)
    
    max_index = len(products_with_feedback)
    
    choice = None
    selection_running = True
    for _ in range(100000): # Menu loop
        if not selection_running:
            return
            
        choice_input = input(f"Enter choice (0-{max_index}) or 'exit' to return: ").strip().lower()
        
        if choice_input == 'exit':
            selection_running = False
            return
        
        # We need a robust check here because get_int_input prompts again
        try:
            choice_int = int(choice_input)
            if 0 <= choice_int <= max_index:
                choice = choice_int
                break
            else:
                print(f"Invalid choice. Please enter a number between 0 and {max_index} or 'exit'.")
        except ValueError:
            print("Invalid input. Please enter a number or 'exit'.")
        
    if choice is None:
        return

    selected_product = None
    if choice > 0:
        selected_product = products_with_feedback[choice]
    
    # 2. Construct SQL query with filtering and ordering (ASC for newest at bottom)
    cursor = db.cursor(dictionary=True)
    base_query = """
    SELECT f.product_name, f.rating, f.comment, c.username, f.timestamp, f.manager_rel 
    FROM feedback f JOIN customers c ON f.customer_id = c.id
    """
    params = []
    
    if selected_product:
        print(f"\n--- Showing Feedback for: {selected_product} (Newest at Bottom) ---")
        base_query += " WHERE f.product_name = %s"
        params.append(selected_product)
        # Use filtered display widths
        comment_width, reply_width, total_width = 45, 45, 120
        row_format = f"{{:<20}} {{:<10}} {{:<{comment_width}}} {{:<{reply_width}}}"
    else:
        print("\n--- Showing Feedback for: ALL Products (Newest at Bottom) ---")
        # Use wide display widths for ALL products
        comment_width, reply_width, total_width = 40, 40, 145
        row_format = f"{{:<20}} {{:<30}} {{:<10}} {{:<{comment_width}}} {{:<{reply_width}}}"

    # Order by ASC (Ascending) ensures newest entries are at the bottom
    base_query += " ORDER BY f.timestamp ASC" 
    
    cursor.execute(base_query, tuple(params))
    feedback_records = cursor.fetchall()
    cursor.close()
    
    if not feedback_records:
        if selected_product:
            print(f"No feedback found for {selected_product}.")
        else:
            print("No feedback submitted yet.")
        return

    df = pd.DataFrame(feedback_records)
    
    # 3. Display comments and replies with correct headers and formatting
    print("\nCustomer Reviews:")
    
    # Header format definition
    if selected_product:
        header_format = f"{'Time':<20} {'Rating':<10} {'Customer Comment':<{comment_width}} {'Manager Reply':<{reply_width}}"
    else:
        header_format = f"{'Time':<20} {'Product':<30} {'Rating':<10} {'Customer Comment':<{comment_width}} {'Manager Reply':<{reply_width}}"

    print(header_format)
    print("-" * total_width)
    
    for _, row in df.iterrows():
        comment_text = row['comment'] if row['comment'] else ""
        reply_text = row['manager_rel'] if row['manager_rel'] else "No reply"

        # Truncate for display
        comment_excerpt = comment_text[:comment_width-3] + '...' if len(comment_text) > comment_width else comment_text
        reply_excerpt = reply_text[:reply_width-3] + '...' if len(reply_text) > reply_width else reply_text

        if selected_product:
            print(row_format.format(
                row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 
                row['rating'], 
                comment_excerpt, 
                reply_excerpt))
        else:
            print(row_format.format(
                row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                row['product_name'],
                row['rating'],
                comment_excerpt,
                reply_excerpt))
    
    print("-" * total_width)

def display_ratings_plot(db, get_int_input):
    """
    Prompts the manager to select a product (or all) and generates relevant rating plots.
    """
    print("\n--- Generating Product Ratings Graphs ---")
    
    db = connect_to_database_safe() 
    if db is None:
        return

    try:
        cursor = db.cursor(dictionary=True)
        # 1. Fetch products with feedback for the menu
        cursor.execute("SELECT DISTINCT product_name FROM feedback WHERE rating IS NOT NULL ORDER BY product_name ASC")
        product_names_list = [d['product_name'] for d in cursor.fetchall()]
        
        if not product_names_list:
            print("No rating data available to plot.")
            cursor.close()
            db.close()
            return

        # 2. Present selection menu
        print("\nSelect the product for plotting trends:")
        print(" [0] View ALL Products (Combined & Individual Trends)")
        products_map = {i + 1: name for i, name in enumerate(product_names_list)}
        for key, name in products_map.items():
            print(f" [{key}] {name}")
        print("-" * 40)
        
        max_index = len(products_map)
        selected_product_name = None
        
        while True: 
            choice_input = get_int_input(f"Enter choice (0-{max_index}): ", min_val=0, max_val=max_index)
            
            if choice_input is None:
                continue
                
            if choice_input == 0:
                selected_product_name = None # Represents 'All Products'
                break
            else:
                selected_product_name = products_map[choice_input]
                break
        
        # 3. Construct SQL Query based on selection
        query = """
        SELECT
            f.rating,
            f.timestamp as feedback_date, 
            f.product_name
        FROM
            feedback f
        WHERE
            f.rating IS NOT NULL AND f.timestamp IS NOT NULL
        """
        params = []
        
        if selected_product_name:
            query += " AND f.product_name = %s"
            params.append(selected_product_name)

        cursor.execute(query, tuple(params))
        data = cursor.fetchall()
        cursor.close()
        
        if not data:
            print(f"No rating data found for plotting for {selected_product_name}.")
            db.close()
            return
            
        df = pd.DataFrame(data)
        df['feedback_date'] = pd.to_datetime(df['feedback_date'])


        # ----------------------------------------------------------------------
        # 4. Calculate Average & Determine Titles
        # ----------------------------------------------------------------------
        overall_average = df['rating'].mean()

        if selected_product_name:
            print(f"\n[i] Overall Average Rating for {selected_product_name}: {overall_average:.2f} / 5.0")
            trend_title = f"Monthly Rating Trend for: {selected_product_name}"
            
        else:
            print(f"\n[i] Overall Average Rating Across All Products and Time: {overall_average:.2f} / 5.0")
            trend_title = "Monthly Rating Trend for Individual Products"
        
        
        # ----------------------------------------------------------------------
        # 5. Trend Graph Generation (Single)
        # ----------------------------------------------------------------------
        
        plt.figure(figsize=(12, 6))

        if selected_product_name:
            # Case: Single Product Trend
            monthly_trend = df.groupby(df['feedback_date'].dt.to_period('M'))['rating'].mean().reset_index()
            monthly_trend['period'] = monthly_trend['feedback_date'].astype(str)
            
            plt.plot(monthly_trend['period'], monthly_trend['rating'], 
                     marker='o', linestyle='-', color='red', label=selected_product_name)
            
            # Set x-ticks
            tick_indices = range(0, len(monthly_trend), max(1, len(monthly_trend) // 10))
            plt.xticks(monthly_trend['period'].iloc[tick_indices], rotation=45, ha='right')
            
        else:
           print("select a product")
        plt.title(trend_title)
        plt.xlabel('Period (Year-Month)')
        plt.ylabel('Average Rating')
        plt.ylim(0, 5.5) 
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.show()

        # ----------------------------------------------------------------------
        # 6. Comparison Bar Plot (Only shown for ALL products)
        # ----------------------------------------------------------------------
        if not selected_product_name:
            
            product_avg_ratings = df.groupby('product_name')['rating'].mean().sort_values(ascending=False).reset_index()
            
            plt.figure(figsize=(12, 6))
            plt.barh(product_avg_ratings['product_name'], product_avg_ratings['rating'], color='teal')
            plt.xlabel('Average Rating')
            plt.ylabel('Product Name')
            plt.title('Lifetime Average Rating for Individual Products (Comparison)')
            plt.xlim(0, 5) 
            plt.gca().invert_yaxis() 
            plt.tight_layout()
            plt.show()

    except Exception as e:
        print(f"\n[!!! Runtime Error !!!] An error occurred during plotting: {e}")
        print("HINT: Ensure the 'feedback' table has data and the 'timestamp' column is valid.")
    finally:
        if db and db.is_connected():
            db.close()
            print("Database connection closed.")
            
def open_feedback_report():
    """
    Manager portal for viewing and managing feedback.
    """
    db = connect_to_database_safe()
    if db is None:
        return
        
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT product_name FROM feedback ORDER BY product_name ASC")
    product_names = [d['product_name'] for d in cursor.fetchall()]
    cursor.close()
    
    if not product_names:
        print("\nNo customer feedback has been submitted yet.")
        db.close()
        return

    running = True
    for _ in range(100000): # Manager Feedback Menu Loop
        if not running:
            db.close()
            return
            
        print("\n" + "="*50)
        print("--- Customer Feedback Management ---")
        print("="*50)
        print("1. View Customer Reviews & Manager Replies (Newest at Bottom)")
        print("2. View Average Product Rating Graph")
        print("3. Reply to Customer Feedback")
        print("4. Return to Manager Main Menu")
        print("-" * 50)
        
        choice = input("Enter choice (1-4): ")
        
        if choice == '1':
            display_feedback_reviews(db, product_names, get_int_input)
        
        elif choice == '2':
            display_ratings_plot(db, get_int_input)
            
        elif choice == '3':
            handle_feedback_reply(db, product_names, get_int_input, input)
        
        elif choice == '4':
            running = False # Exit flag
            db.close()
            return # Exit the function
        
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")


def manager_portal(user):
    portal_running = True
    for _ in range(100000):
        if not portal_running:
            return
            
        print("\n" + "="*50)
        print(f"Welcome, {user['username']}! (Manager Portal)")
        print("="*50)
        print("1. View Sales Report & Trend")
        print("2. View & Update Inventory")
        print("3. View Registered Customers")
        print("4. Add New Manager")
        print("5. Manually Log Sale (Historical/Adjustments)")
        print("6. View Customer Feedback Report (with Plot)")
        print("7. Logout")
        print("-" * 50)
        
        
        choice = input("Enter choice (1-7): ")
        
        if choice == '7':
            print("Logging out.")
            portal_running = False
            return
        
        elif choice == '1':
            open_sales_report()
            
        elif choice == '2':
            handle_inventory_update()
            
        elif choice == '3':
            open_customers_view()
            
        elif choice == '4':
            handle_add_manager()
            
        elif choice == '5':
            handle_manual_sale()
            
        elif choice == '6':
            open_feedback_report()
            
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")


# ======================================================================
# 7. Main Application run
# ======================================================================
def run_app():
    """Main function to run the application."""
    setup_database()
    
    current_user = None
    
    for _ in range(100000):
        if current_user is None:
            current_user = auth_portal()
            
        if current_user is not None:
            if current_user['role'] == 'customer':
                customer_portal(current_user)
            elif current_user['role'] == 'manager':
                manager_portal(current_user)
                
            current_user = None 

if __name__ == '__main__':
    run_app()