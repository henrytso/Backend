from db import *
from flask import Flask, request
import json
import boto3
from io import BufferedReader

from enum import Enum

app = Flask(__name__)
db_filename = "cms.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

s3 = boto3.client("s3")
S3_BUCKET = "cmsapp-assignmentsubmissions-useast2"
S3_URI_PREFIX = f"s3://{S3_BUCKET}/"

# Error Response Types
ErrorType = Enum("ErrorType", ["BAD_REQUEST", "NOT_FOUND"])

# Generalized response formats
def success_response(data, code=200):
    return json.dumps(data), code

def failure_response(error_type):
    if error_type == ErrorType.BAD_REQUEST:
        return json.dumps({"error": "Bad request."}), 400
    if error_type == ErrorType.NOT_FOUND:
        return json.dumps({"error": "Resource not found."}), 404
    return json.dumps({"error": "Unknown error."}), 400

# Generalized request body verification
def has_required_fields(body, fields):
    for f in fields:
        if body.get(f) is None:
            return False
    return True

# Routes
@app.route("/api/courses/")
def get_courses():
    courses = Course.query.all()
    return [c.serialize() for c in courses]

@app.route("/api/courses/", methods=["POST"])
def create_course():
    body = json.loads(request.data)
    required_fields = ["code", "name"]
    if not has_required_fields(body, required_fields):
        return failure_response(ErrorType.BAD_REQUEST)
    course = Course(code=body.get("code"), name=body.get("name"))
    db.session.add(course)
    db.session.commit()
    return success_response(course.serialize())

@app.route("/api/courses/<int:course_id>/")
def get_course(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response(ErrorType.NOT_FOUND)
    return success_response(course.serialize())

@app.route("/api/courses/<int:course_id>/", methods=["DELETE"])
def delete_course(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response(ErrorType.NOT_FOUND)
    db.session.delete(course)
    db.session.commit()
    return success_response(course.serialize())

@app.route("/api/users/", methods=["POST"])
def create_user():
    body = json.loads(request.data)
    fields = ["name", "netid"]
    if not has_required_fields(body, fields):
        return failure_response(ErrorType.BAD_REQUEST)
    user = User(name=body.get("name"), netid=body.get("netid"))
    db.session.add(user)
    db.session.commit()
    return success_response(user.serialize())

@app.route("/api/courses/<int:course_id>/", methods=["POST"])
def add_user_to_course(course_id):
    body = json.loads(request.data)
    fields = ["user_id", "type"]
    if not has_required_fields(body, fields):
        return failure_response(ErrorType.BAD_REQUEST)
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response(ErrorType.NOT_FOUND)
    user = User.query.filter_by(id=body.get("user_id")).first()
    if user is None:
        return failure_response(ErrorType.NOT_FOUND)
    if body.get("type") == "instructor":
        course.instructors.append(user)
    elif body.get("type") == "student":
        course.students.append(user)
    else:
        return failure_response(ErrorType.BAD_REQUEST)
    db.session.commit()
    return success_response(course.serialize())

@app.route("/api/courses/<int:course_id>/assignment/", methods=["POST"])
def create_assignment(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return failure_response(ErrorType.NOT_FOUND)
    body = json.loads(request.data)
    fields = ["title", "due_date"]
    if not has_required_fields(body, fields):
        return failure_response(ErrorType.BAD_REQUEST)
    assignment = Assignment(title=body.get("title"), due_date=body.get("due_date"), course_id=course_id)
    db.session.add(assignment)
    course.assignments.append(assignment)
    db.session.commit()
    return success_response(assignment.serialize())

# Old route: request body is raw JSON.
# The "content" field of the body is a string, which will be stored in the Submission "content" field.
#@app.route("/api/assignments/<int:assignment_id>/submit/", methods=["POST"])
#def submit_assigment(assignment_id):
#    assignment = Assignment.query.filter_by(id=assignment_id).first()
#    if assignment is None:
#        return failure_response(ErrorType.NOT_FOUND)
#    body = json.loads(request.data)
#    fields = ["content", "user_id"]
#    if not has_required_fields(body, fields):
#        return failure_response(ErrorType.BAD_REQUEST)
#    user = User.query.filter_by(id=body.get("user_id")).first()
#    if user is None:
#        return failure_response(ErrorType.NOT_FOUND)
#    course = Course.query.filter_by(id=assignment.course_id).first()
#    if user not in course.students:
#        return failure_response(ErrorType.BAD_REQUEST)
#    submission = Submission(content=body.get("content"), user_id=body.get("user_id"), assignment_id=assignment_id)
#    db.session.add(submission)
#    db.session.commit()
#    return success_response(submission.serialize())

# New route: request body is form-data.
# The "content" field of the body is a file. The file is uploaded to AWS S3, and the Submission "content" field will
#   contain the url of the resource in the S3 bucket.
@app.route("/api/assignments/<int:assignment_id>/submit/", methods=["POST"])
def submit_assigment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id).first()
    if assignment is None:
        return failure_response(ErrorType.NOT_FOUND)
    user_id = request.form.get("user_id")
    content = request.files.get("content")
    if user_id is None or content is None:
        return failure_response(ErrorType.BAD_REQUEST)
    course = Course.query.filter_by(id=assignment.course_id).first()
    user = User.query.filter_by(id=user_id).first()
    previous_submissions = Submission.query.filter_by(user_id=user_id, assignment_id=assignment_id)
    submission_count = previous_submissions.count() + 1
    RESOURCE_URI_SUFFIX = f"{course.code}/{assignment.title}/{user.netid}/Submission{submission_count}"
    with BufferedReader(content) as content:
        s3.upload_fileobj(content, S3_BUCKET, RESOURCE_URI_SUFFIX)
    content_uri = S3_URI_PREFIX + RESOURCE_URI_SUFFIX
    submission = Submission(content=content_uri, user_id=user_id, assignment_id=assignment_id)
    db.session.add(submission)
    db.session.commit()
    return success_response(submission.serialize())


@app.route("/api/assignments/<int:assignment_id>/grade/", methods=["POST"])
def grade_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id).first()
    if assignment is None:
        return failure_response(ErrorType.NOT_FOUND)
    body = json.loads(request.data)
    fields = ["submission_id", "score"]
    if not has_required_fields(body, fields):
        return failure_response(ErrorType.BAD_REQUEST)
    submission = Submission.query.filter_by(id=body.get("submission_id")).first()
    if submission is None:
        return failure_response(ErrorType.NOT_FOUND)
    submission.score = body.get("score")
    db.session.commit()
    return success_response(submission.serialize())
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
