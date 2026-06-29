CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);

INSERT INTO items (name, description) VALUES ('Item 1', 'Description of Item 1');
INSERT INTO items (name, description) VALUES ('Item 2', 'Description of Item 2');
INSERT INTO items (name, description) VALUES ('Item 3', 'Description of Item 3');