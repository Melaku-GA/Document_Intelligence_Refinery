import sqlite3
import os

class FactTable:
    def __init__(self, db_path: str = ".refinery/fact_table.db"):
        os.makedirs(".refinery", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._prepare_table()

    def _prepare_table(self):
        cursor = self.conn.cursor()
        # Create a structured table for financial metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric TEXT,
                value REAL,
                unit TEXT,
                period TEXT,
                source_doc TEXT
            )
        """)
        self.conn.commit()

    def add_fact(self, metric, value, unit, period, source):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO financial_facts (metric, value, unit, period, source_doc) VALUES (?, ?, ?, ?, ?)",
            (metric, value, unit, period, source)
        )
        self.conn.commit()