DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS docs;
DROP TABLE IF EXISTS history;
DROP TABLE IF EXISTS docs_list;

CREATE TABLE user(
  id text,
  password text,
  name text,
  grade integer,
  assign_date numeric,
  PRIMARY KEY (id)
);

CREATE TABLE docs_list(
  id integer,
  name text,
  date numeric,
  PRIMARY KEY (id)
);

CREATE TABLE docs(
  id integer,
  html_data text,
  PRIMARY KEY (id)
  FOREIGN KEY (id) REFERENCES docs_list(id)
);

CREATE TABLE history(
  id integer,
  version integer,
  markdown_data text,
  date numeric,
  PRIMARY KEY (id, version),
  FOREIGN KEY (id) REFERENCES docs_list (id)
);