DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS request;
DROP TABLE IF EXISTS bid;
DROP TABLE IF EXISTS location;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    company TEXT NOT NULL,
    user_type TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_by INTEGER NOT NULL,
    collection_date TIMESTAMP NOT NULL,
    delivery_date TIMESTAMP NOT NULL,
    collection_address TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    pallets INTEGER NOT NULL,
    weight INTEGER NOT NULL,
    company TEXT NOT NULL,
    request_status TEXT NOT NULL DEFAULT "Awaiting bids",
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user (id)
);

CREATE TABLE bid (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    bid_amount INTEGER NOT NULL,
    bid_status INTEGER NOT NULL DEFAULT "Awaiting response",
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES request (id),
    FOREIGN KEY (created_by) REFERENCES user (id)
);

CREATE TABLE location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_by INTEGER NOT NULL,
    name TEXT NOT NULL,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    zipcode TEXT NOT NULL,
    created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user (id)
);

