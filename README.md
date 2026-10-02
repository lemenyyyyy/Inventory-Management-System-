[README.md](https://github.com/user-attachments/files/32957071/README.md)
# 🍫 Chocolate Apocalypse — Inventory Management System

<p align="center">
  <strong>A Python + MySQL inventory, sales, customer, and feedback management system for a chocolate shop.</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="MySQL" src="https://img.shields.io/badge/MySQL-8.0%2B-4479A1?logo=mysql&logoColor=white">
  <img alt="Pandas" src="https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white">
  <img alt="Matplotlib" src="https://img.shields.io/badge/Matplotlib-3.x-11557C">
  <img alt="License" src="https://img.shields.io/badge/License-Add%20your%20license-lightgrey">
</p>

## 📌 Overview

**Chocolate Apocalypse** is a command-line inventory and sales management application designed for a chocolate shop.

The system provides separate customer and manager portals and connects to MySQL for persistent customer, manager, sales, and feedback data. Product inventory is persisted locally.

## ✨ Features

### 🛒 Customer Portal
- Browse chocolates, pralines, and cakes
- Add products to a shopping cart
- Check stock availability
- Checkout and record sales
- Submit product ratings and feedback
- Logout safely from the customer portal

### 🧑‍💼 Manager Portal
- View sales reports and trends
- View and update inventory
- View registered customers
- Add managers
- Manually log historical/adjustment sales
- Review customer feedback
- Reply to customer feedback
- View rating visualizations

### 📊 Reporting
- Product sales history
- Sales trend visualizations
- Average product ratings
- Product comparison charts

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| MySQL | Persistent application data |
| Pandas | Product/reporting data processing |
| Matplotlib | Sales and rating visualizations |
| python-dotenv | Environment-based configuration |
| pytest | Testing foundation |

## 📁 Project Structure

```text
chocolate-apocalypse-inventory/
├── src/
│   ├── __init__.py
│   └── app.py
├── sql/
│   └── schema.sql
├── docs/
│   └── screenshots/
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 🖥️ Screenshots

> Add screenshots of the running application to `docs/screenshots/`.

### Customer Portal

![Customer Portal](docs/screenshots/customer-portal.png)

### Manager Portal

![Manager Portal](docs/screenshots/manager-portal.png)

### Sales / Rating Reports

![Reports](docs/screenshots/reports.png)

If screenshots are not available yet, the application can still be run from the command line and screenshots can be added later.

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/chocolate-apocalypse-inventory.git
cd chocolate-apocalypse-inventory
```

### 2. Create a virtual environment

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL

Create the database:

```sql
CREATE DATABASE chocolate_shop;
```

Then initialize the tables using:

```bash
mysql -u root -p chocolate_shop < sql/schema.sql
```

### 5. Configure environment variables

Copy the example configuration:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Update `.env`:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=chocolate_shop
```

**Never commit `.env` to GitHub.**

### 6. Run the application

```bash
python src/app.py
```

## 🧪 Testing

The project includes a `tests/` directory for automated tests.

Run:

```bash
pytest
```

As the application is primarily an interactive CLI/database application, additional integration tests can be added around database operations and business logic.

## 🗄️ Database

The application uses MySQL tables for:

- Customers
- Managers
- Sales
- Feedback

The database schema is included in [`sql/schema.sql`](sql/schema.sql).

## 🔐 Security Notes

Database credentials should be supplied through environment variables rather than committed to source control.

Before publishing a project publicly:

1. Make sure `.env` is ignored.
2. Remove any previously committed credentials.
3. Rotate credentials that may have been exposed previously.
4. Use dedicated database users with only the permissions the application needs.

## 🚀 Future Improvements

Potential next steps for the project include:

- Web-based UI
- REST API
- Role-based authorization improvements
- Password hashing
- Automated database migrations
- Better automated test coverage
- Docker support
- CI with GitHub Actions
- Product image management
- Exportable PDF/CSV reports

## 📜 License

No license has been selected for this project yet.

If you intend to make the repository open source, add an appropriate `LICENSE` file.

## 👤 Author

**Your Name**

Replace this section with your GitHub profile and project links.

---

⭐ If this project is useful to you, consider giving the repository a star!
