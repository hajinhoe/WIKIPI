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

CREATE TABLE doc_list(
  id integer,
  name text,
  date numeric,
  PRIMARY KEY (id)
);

CREATE TABLE doc(
  id integer,
  html_data text,
  markdown_data text,
  PRIMARY KEY (id),
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

CREATE TABLE reverse_link(
  id integer,
  referencing integer,
  PRIMARY KEY (id, referencing),
  FOREIGN KEY (id) REFERENCES docs_list (id),
  FOREIGN KEY (referencing) REFERENCES docs_list (id)
)