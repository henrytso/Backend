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
        """
        Secures a connection with the database and stores the connection.
        """
        self.conn = sqlite3.connect("todo.db", check_same_thread=False)
        self.create_task_table()


    def create_task_table(self):
        """
        Create a task table.
        """
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS task(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                done BOOLEAN NOT NULL
            );
        """)


    def delete_task_table(self):
        """
        Deletes the task table.
        """
        self.conn.execute("""
            DROP TABLE IF EXISTS task;
        """)


    def get_all_tasks(self):
        """
        Returns all tasks in task table.
        """
        cursor = self.conn.execute("""
            SELECT * FROM task;
        """)
        tasks = []
        for row in cursor:
            tasks.append({"id": row[0], "description": row[1], "done": bool(row[2])})
        return tasks


    def insert_task_table(self, description, done):
        """
        Inserts a row into the task table.
        """
        cursor = self.conn.execute("""
            INSERT INTO task (description, done)
            VALUES (?, ?);
        """, (description, done))
        self.conn.commit()
        return cursor.lastrowid


    def get_task_by_id(self, task_id):
        """
        Returns the task with id [task_id], if it exists.
        """
        cursor = self.conn.execute("""
            SELECT * FROM task WHERE id = (?);
        """, (task_id,))
        for row in cursor:
            task = {"id": row[0], "description": row[1], "done": bool(row[2])}
            return task
        return None


    def update_task_by_id(self, task_id, description, done):
        """
        Updates the task with id [task_id] to have new description [description] and new done [done].
        """
        self.conn.execute("""
            UPDATE task
            SET description = ?,
            done = ?
            WHERE id = ?;
        """, (description, done, task_id))
        self.conn.commit()


    def delete_task_by_id(self, task_id):
        """
        Deletes the task with id [task_id].
        """
        self.conn.execute("""
            DELETE FROM task
            WHERE id = ?;
        """, (task_id,))
        self.conn.commit()


# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)
