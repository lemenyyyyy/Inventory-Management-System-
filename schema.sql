CREATE DATABASE IF NOT EXISTS chocolate_shop;
USE chocolate_shop;

CREATE TABLE IF NOT EXISTS customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    mobile VARCHAR(15) UNIQUE,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS managers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS sales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME,
    product_name VARCHAR(255),
    quantity INT,
    unit_price DECIMAL(10, 2),
    total DECIMAL(10, 2)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    product_name VARCHAR(255),
    rating INT,
    comment TEXT,
    timestamp DATETIME,
    manager_rel VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
