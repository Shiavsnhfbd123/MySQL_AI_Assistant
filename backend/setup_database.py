"""Create or repair the restricted MySQL application account without exposing passwords."""

from getpass import getpass
import re

import mysql.connector

from app.config import settings


SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")
PRIVILEGES = (
    "SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, "
    "REFERENCES, CREATE VIEW, SHOW VIEW"
)


def require_safe_identifier(value: str, label: str) -> str:
    if not SAFE_IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} may contain only letters, numbers, and underscores.")
    return value


def main() -> None:
    database = require_safe_identifier(settings.mysql_database, "MYSQL_DATABASE")
    app_user = require_safe_identifier(settings.mysql_user, "MYSQL_USER")
    if not settings.mysql_password:
        raise RuntimeError("Set MYSQL_PASSWORD in backend/.env before running setup.")

    print("MySQL AI Assistant database repair")
    print(f"Server: {settings.mysql_host}:{settings.mysql_port}")
    print(f"Database: {database}")
    print(f"Application user: {app_user}@localhost")
    admin_user = input("MySQL administrator [root]: ").strip() or "root"
    admin_password = getpass("Administrator password (hidden): ")

    connection = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=admin_user,
        password=admin_password,
        autocommit=False,
        connection_timeout=settings.mysql_connect_timeout,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.execute(
            "CREATE USER IF NOT EXISTS %s@%s IDENTIFIED BY %s",
            (app_user, "localhost", settings.mysql_password),
        )
        cursor.execute(
            "ALTER USER %s@%s IDENTIFIED BY %s",
            (app_user, "localhost", settings.mysql_password),
        )
        cursor.execute(
            f"GRANT {PRIVILEGES} ON `{database}`.* TO %s@%s",
            (app_user, "localhost"),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    verification = mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        connection_timeout=settings.mysql_connect_timeout,
    )
    verification.close()
    print("Success: database and restricted application account are ready.")


if __name__ == "__main__":
    try:
        main()
    except mysql.connector.Error as exc:
        print(f"MySQL setup failed ({exc.errno}): {exc.msg}")
        raise SystemExit(1) from None
    except (RuntimeError, ValueError) as exc:
        print(f"Setup failed: {exc}")
        raise SystemExit(1) from None
