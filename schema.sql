DROP TABLE IF EXISTS user_ip_tags;

CREATE TABLE user_ip_tags (
   ip VARCHAR(255) NOT NULL,
   tags TEXT
);
