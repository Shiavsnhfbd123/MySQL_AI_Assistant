-- Run this once as a MySQL administrator. Change the password before executing.
CREATE DATABASE IF NOT EXISTS mysql_ai_lab
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'mysql_ai_assistant'@'localhost'
  IDENTIFIED BY 'replace_with_a_strong_password';

-- Also repair the password when the account already exists.
ALTER USER 'mysql_ai_assistant'@'localhost'
  IDENTIFIED BY 'replace_with_a_strong_password';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES,
      CREATE VIEW, SHOW VIEW
ON mysql_ai_lab.* TO 'mysql_ai_assistant'@'localhost';

FLUSH PRIVILEGES;
