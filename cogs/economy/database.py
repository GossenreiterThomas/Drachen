import sqlite3

class EconomyDB:
    def __init__(self, path="economy.db"):
        self.conn = sqlite3.connect(path)
        self.c = self.conn.cursor()
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER PRIMARY KEY,
                wallet INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                last_work REAL DEFAULT 0,
                last_daily REAL DEFAULT 0
            )
        """)
        self.conn.commit()

    def get_user(self, user_id):
        self.c.execute("SELECT wallet, bank, last_work, last_daily FROM economy WHERE user_id = ?", (user_id,))
        row = self.c.fetchone()
        if not row:
            self.c.execute("INSERT INTO economy (user_id, wallet, bank, last_work, last_daily) VALUES (?, 0, 0, 0, 0)", (user_id,))
            self.conn.commit()
            return (0, 0, 0, 0)
        return row

    def update_balance(self, user_id, wallet=None, bank=None, last_work=None, last_daily=None):
        fields, params = [], []
        if wallet is not None:
            fields.append("wallet = ?")
            params.append(wallet)
        if bank is not None:
            fields.append("bank = ?")
            params.append(bank)
        if last_work is not None:
            fields.append("last_work = ?")
            params.append(last_work)
        if last_daily is not None:
            fields.append("last_daily = ?")
            params.append(last_daily)

        params.append(user_id)
        set_clause = ", ".join(fields)
        self.c.execute(f"UPDATE economy SET {set_clause} WHERE user_id = ?", tuple(params))
        self.conn.commit()
