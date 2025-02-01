-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  nickname TEXT UNIQUE NOT NULL
);

-- edited from post table to joke table
CREATE TABLE joke (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  author_id INTEGER NOT NULL,
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (title, author_id),
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE joke_rating (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  joke_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  rating INTEGER CHECK(rating >= 1 AND rating <= 5),
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (joke_id) REFERENCES joke (id),
  FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE user_joke (
    user_id INTEGER NOT NULL,
    joke_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, joke_id),
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (joke_id) REFERENCES joke (id)
);
ALTER TABLE user ADD COLUMN joke_balance INTEGER DEFAULT 0;