from app.services import sql_executor


class FakeCursor:
    with_rows = False
    rowcount = 2
    lastrowid = 11

    def execute(self, sql, parameters):
        self.executed = (sql, parameters)

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_value = FakeCursor()
        self.committed = False
        self.closed = False

    def cursor(self, dictionary=False):
        assert dictionary
        return self.cursor_value

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        self.closed = True


def test_executor_commits_write(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(sql_executor, "get_connection", lambda: connection)
    result = sql_executor.execute_sql("UPDATE students SET age=%s WHERE id=%s", [21, 1])
    assert result["affected_rows"] == 2
    assert connection.committed
    assert connection.closed
