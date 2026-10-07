import mysql.connector
from mysql.connector import MySQLConnection
from urllib.parse import unquote, urlparse

from app.config import settings


def _connection_options() -> dict[str, object]:
    options = {
        "host": settings.mysql_host,
        "port": settings.mysql_port,
        "user": settings.mysql_user,
        "password": settings.mysql_password,
        "database": settings.mysql_database,
        "autocommit": False,
        "connection_timeout": settings.mysql_connect_timeout,
        "ssl_disabled": settings.mysql_ssl_disabled,
        "ssl_verify_cert": settings.mysql_ssl_verify_cert,
        "ssl_verify_identity": settings.mysql_ssl_verify_identity,
    }
    if settings.mysql_url:
        parsed = urlparse(settings.mysql_url)
        if parsed.scheme not in {"mysql", "mysql+mysqlconnector"}:
            raise ValueError("MYSQL_URL must use the mysql:// scheme.")
        if not parsed.hostname or not parsed.username or not parsed.path.strip("/"):
            raise ValueError("MYSQL_URL must include user, host, and database name.")
        options.update(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=unquote(parsed.username),
            password=unquote(parsed.password or ""),
            database=unquote(parsed.path.lstrip("/")),
        )
    if settings.mysql_ssl_ca:
        options["ssl_ca"] = settings.mysql_ssl_ca
    return options


def get_connection() -> MySQLConnection:
    options = _connection_options()

    return mysql.connector.connect(
        **options,
    )
