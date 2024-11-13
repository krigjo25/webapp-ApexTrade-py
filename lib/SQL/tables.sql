CREATE TABLE IF NOT EXISTS ? (

    --  User's Trading portefolio
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    abbrivation TEXT NOT NULL,
    qty INT NOT NULL,
    price REAL NOT NULL,
    total REAL NOT NULL,
    UNIQUE (abbrivation));

CREATE TABLE trading_history (

    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                user_id INTEGER NOT NULL,
                                abbrivation TEXT NOT NULL,
                                status TEXT NOT NULL DEFAULT UNKOWN,
                                qty INT NOT NULL,
                                price REAL NOT NULL,
                                time_stamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users(id));
