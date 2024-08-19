from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

course_instructors = db.Table(
    "course_instructors",
    db.Model.metadata,
    db.Column("instructor_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("course_id", db.Integer, db.ForeignKey("course.id"))
)

course_students = db.Table(
    "course_students",
    db.Model.metadata,
    db.Column("student_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("course_id", db.Integer, db.ForeignKey("course.id"))
)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    netid = db.Column(db.String, nullable=False)
    courses_teaching = db.relationship("Course", secondary=course_instructors, back_populates="instructors")
    courses_taking = db.relationship("Course", secondary=course_students, back_populates="students")

    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.netid = kwargs.get("netid")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
            "courses": [c.simple_serialize() for c in self.courses_teaching] + [c.simple_serialize() for c in self.courses_taking]
        }

    def simple_serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid
        }
        

class Course(db.Model):
    __tablename__ = "course"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    assignments = db.relationship("Assignment", cascade="delete")
    instructors = db.relationship("User", secondary=course_instructors, back_populates="courses_teaching")
    students = db.relationship("User", secondary=course_students, back_populates="courses_taking")

    def __init__(self, **kwargs):
        self.code = kwargs.get("code")
        self.name = kwargs.get("name")

    def serialize(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "assignments": [a.simple_serialize() for a in self.assignments],
            "instructors": [u.simple_serialize() for u in self.instructors],
            "students": [u.simple_serialize() for u in self.students]
        }

    def simple_serialize(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name
        }


class Assignment(db.Model):
    __tablename__ = "assignment"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    due_date = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    
    def __init__(self, **kwargs):
        self.title = kwargs.get("title")
        self.due_date = kwargs.get("due_date")
        self.course_id = kwargs.get("course_id")
    
    def serialize(self):
        course = Course.query.filter_by(id=self.course_id).first()
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date,
            "course": course.simple_serialize()
        }

    def simple_serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date
        }


class Submission(db.Model):
    __tablename__ = "submission"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    score = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"), nullable=False)
    
    def __init__(self, **kwargs):
        self.content = kwargs.get("content")
        self.user_id = kwargs.get("user_id")
        self.assignment_id = kwargs.get("assignment_id")

    def serialize(self):
        user = User.query.filter_by(id=self.user_id).first()
        assignment = Assignment.query.filter_by(id=self.assignment_id).first()
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "user": user.simple_serialize(),
            "assignment": assignment.simple_serialize()
        }
    
    def simple_serialize(self):
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "user_id": self.user_id,
            "assignment_id": self.assignment_id
        }
