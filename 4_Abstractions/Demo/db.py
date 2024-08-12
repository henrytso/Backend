from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# implement database model classes

association_table = db.Table(
    "association",
    db.Model.metadata,
    db.Column("task_id", db.Integer, db.ForeignKey("task.id")),
    db.Column("category_id", db.Integer, db.ForeignKey("category.id"))
)

class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String, nullable=False)
    done = db.Column(db.Boolean, nullable=False)
    subtasks = db.relationship("Subtask", cascade="delete")
    categories = db.relationship("Category", secondary=association_table, back_populates="tasks")

    def __init__(self, **kwargs):
        """
        Initialize the Task object/entry
        """
        self.description = kwargs.get("description", "")
        self.done = kwargs.get("done", False)

    def serialize(self):
        return {
            "id": self.id,
            "description": self.description,
            "done": self.done,
            "subtasks": [s.serialize() for s in self.subtasks],
            "categories": [c.simple_serialize() for c in self.categories]
        }

    def simple_serialize(self):
        return {
            "id": self.id,
            "description": self.description,
            "done": self.done,
            "subtasks": [s.serialize() for s in self.subtasks]
        }


class Subtask(db.Model):
    __tablename__ = "subtask"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String, nullable=False)
    done = db.Column(db.Boolean, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)

    def __init__(self, **kwargs):
        self.description = kwargs.get("description", "")
        self.done = kwargs.get("done", False)
        self.task_id = kwargs.get("task_id")

    def serialize(self):
        return {
            "id": self.id,
            "description": self.description,
            "done": self.done,
            "task_id": self.task_id
        }


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String, nullable=False)
    tasks = db.relationship("Task", secondary=association_table, back_populates="categories")

    def __init__(self, **kwargs):
        self.description = kwargs.get("description")

    def serialize(self):
        return {
            "id": self.id,
            "description": self.description,
            "tasks": [t.simple_serialize() for t in self.tasks]
        }

    def simple_serialize(self):
        return {
            "id": self.id,
            "description": self.description
        }

