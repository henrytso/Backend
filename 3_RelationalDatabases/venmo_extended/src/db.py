import os
import sqlite3

# From: https://goo.gl/YzypOI
def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class DatabaseDriver(object):
    """
    Database driver for the Task app.
    Handles with reading and writing data with the database.
    """

    def __init__(self):
        self.conn = sqlite3.connect("venmo.db", check_same_thread=False)
        self.conn.execute("""PRAGMA foreign_keys = 1""")
        self.create_user_table()
        self.create_txn_table()


    def create_user_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL,
                balance INTEGER
            );
        """)


    def delete_user_table(self):
        self.conn.execute("""
            DROP TABLE IF EXISTS user;
        """)


    def get_all_users(self):
        cursor = self.conn.execute("""
            SELECT * FROM user;
        """)
        users = []
        for row in cursor:
            users.append({"id": row[0], "name": row[1], "username": row[2], "balance": row[3]})
        return users


    def insert_user_table(self, name, username, balance):
        cursor = self.conn.execute("""
            INSERT INTO user (name, username, balance)
            VALUES (?, ?, ?);
        """, (name, username, balance))
        self.conn.commit()
        return cursor.lastrowid


    def get_user_by_id(self, user_id):
        cursor = self.conn.execute("""
            SELECT * FROM user
            WHERE id = (?);
        """, (user_id,))
        for row in cursor:
            return {
                "id": row[0],
                "name": row[1],
                "username": row[2],
                "balance": row[3],
                "transactions": self.get_txns_by_user_id(user_id)
            }
        return None


    def delete_user_by_id(self, user_id):
        self.conn.execute("""
            DELETE FROM user
            WHERE id = (?);
        """, (user_id,))
        self.conn.commit()


    def transfer_user_balance(self, sender_id, receiver_id, amount):
        self.conn.execute("""
            UPDATE user
            SET balance = balance - ?
            WHERE id = ?;
        """, (amount, sender_id))
        self.conn.execute("""
            UPDATE user
            SET balance = balance + ?
            WHERE id = ?;
        """, (amount, receiver_id))
        self.conn.commit()


    def create_txn_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS txn(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                message TEXT,
                accepted BOOLEAN,
                FOREIGN KEY(sender_id) REFERENCES user(id),
                FOREIGN KEY(receiver_id) REFERENCES user(id)
            );
        """)


    def insert_txn_table(self, sender_id, receiver_id, amount, message, accepted):
        cursor = self.conn.execute("""
            INSERT INTO txn (sender_id, receiver_id, amount, message, accepted)
            VALUES (?, ?, ?, ?, ?);
        """, (sender_id, receiver_id, amount, message, accepted))
        if accepted:
            self.transfer_user_balance(sender_id, receiver_id, amount)
        self.conn.commit()
        return cursor.lastrowid


    def update_txn(self, txn_id, accepted):
        self.conn.execute("""
            UPDATE txn
            SET timestamp = CURRENT_TIMESTAMP,
            accepted = ?
            WHERE id = ?;
        """, (accepted, txn_id))
        updated_txn = self.get_txn_by_id(txn_id)
        if accepted:
            self.transfer_user_balance(updated_txn["sender_id"], updated_txn["receiver_id"], updated_txn["amount"])
        self.conn.commit()
        return updated_txn


    def get_txn_by_id(self, txn_id):
        cursor = self.conn.execute("""
            SELECT * FROM txn
            WHERE id = ?;
        """, (txn_id,))
        for row in cursor:
            txn = {
                "id": row[0],
                "timestamp": row[1],
                "sender_id": row[2],
                "receiver_id": row[3],
                "amount": row[4],
                "message": row[5],
                "accepted": row[6]
            }
            return txn
        return None


    def get_txns_by_user_id(self, user_id):
        cursor = self.conn.execute("""
            SELECT * FROM txn
            WHERE sender_id = ?
            OR receiver_id = ?;
        """, (user_id, user_id))
        txns = []
        for row in cursor:
            txn = {
                "id": row[0],
                "timestamp": row[1],
                "sender_id": row[2],
                "receiver_id": row[3],
                "amount": row[4],
                "message": row[5],
                "accepted": row[6]
            }
            txns.append(txn)
        return txns


    def get_txns_of_user_join(self, user_id):
        cursor = self.conn.execute("""
            SELECT u1.name as sender_name, u2.name as receiver_name, txn.amount, txn.message, txn.accepted, txn.timestamp
            FROM (
                (
                    (
                        SELECT * FROM txn
                        WHERE sender_id = ?
                        OR receiver_id = ?
                    ) txn
                    INNER JOIN user u1
                    ON sender_id = u1.id
                )
                INNER JOIN user u2
                ON receiver_id = u2.id
            );
        """, (user_id, user_id))
        txns = []
        for row in cursor:
            txn = {
                "sender_name": row[0],
                "receiver_name": row[1],
                "amount": row[2],
                "message": row[3],
                "accepted": row[4],
                "timestamp": row[5],
            }
            txns.append(txn)
        return txns


# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)
