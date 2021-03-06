CREATE TABLE Account(
  account_id INTEGER UNIQUE NOT NULL,
  pseudo VARCHAR(20) UNIQUE NOT NULL,
  password VARCHAR(50) NOT NULL,
  PRIMARY KEY (account_id)
);

CREATE TABLE Object(
  object_id INTEGER UNIQUE NOT NULL,
  owner_id INTEGER NOT NULL,
  PRIMARY KEY (object_id),
  FOREIGN KEY (owner_id) REFERENCES Account (account_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Comment(
  comment_id INTEGER UNIQUE NOT NULL,
  account_id INTEGER NOT NULL,
  object_id INTEGER NOT NULL,
  text VARCHAR(1000) NOT NULL,
  comment_time TIMESTAMP NOT NULL,
  PRIMARY KEY (comment_id),
  FOREIGN KEY (account_id) REFERENCES Account (account_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (object_id) REFERENCES Object (object_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE CanEdit(
  account_id INTEGER NOT NULL,
  object_id INTEGER NOT NULL,
  PRIMARY KEY (account_id, object_id),
  FOREIGN KEY (account_id) REFERENCES Account (account_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (object_id) REFERENCES Object (object_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE Player(
  player_id INTEGER UNIQUE NOT NULL,
  firstname VARCHAR(50) NOT NULL,
  lastname VARCHAR(50) NOT NULL,
  elo_rating INTEGER,
  nationality VARCHAR(3),
  PRIMARY KEY (player_id),
  FOREIGN KEY (player_id) REFERENCES Object (object_id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE Event(
  event_id INTEGER UNIQUE NOT NULL,
  event_name VARCHAR(100) NOT NULL,
  location VARCHAR(100),
  start_date DATE,
  end_date DATE,
  PRIMARY KEY (event_id),
  FOREIGN KEY (event_id) REFERENCES Object (object_id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE Game(
  game_id INTEGER UNIQUE NOT NULL,
  moves BYTEA NOT NULL,
  white_id INTEGER,
  black_id INTEGER,
  start_date DATE,
  location VARCHAR(100),
  event_id INTEGER ,
  result INTEGER NOT NULL,
  PRIMARY KEY (game_id),
  FOREIGN KEY (game_id) REFERENCES Object (object_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  FOREIGN KEY (white_id) REFERENCES Player (player_id) ON DELETE SET NULL ON UPDATE CASCADE,
  FOREIGN KEY (black_id) REFERENCES Player (player_id) ON DELETE SET NULL ON UPDATE CASCADE,
  FOREIGN KEY (event_id) REFERENCES Event (event_id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE Opening(
  opening_id INTEGER UNIQUE NOT NULL,
  moves BYTEA NOT NULL,
  opening_name VARCHAR(100) NOT NULL,
  PRIMARY KEY (opening_id),
  FOREIGN KEY (opening_id) REFERENCES Object (object_id) ON DELETE RESTRICT ON UPDATE RESTRICT
);
