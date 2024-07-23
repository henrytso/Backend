import json
from flask import Flask, request
import db

app = Flask(__name__)

DB = db.DatabaseDriver()


@app.route("/")
@app.route("/tasks/")
def get_tasks():
    return json.dumps({"tasks": DB.get_all_tasks()}), 200


@app.route("/tasks/", methods=["POST"])
def create_task():
    body = json.loads(request.data)
    description = body.get("description")
    done = body.get("done")
    task_id = DB.insert_task_table(description, done)
    task = DB.get_task_by_id(task_id)
    if not task:
        return json.dumps({"error": "Task could not be created."}), 404
    return json.dumps(task), 201


@app.route("/tasks/<int:task_id>/")
def get_task(task_id):
    task = DB.get_task_by_id(task_id)
    if not task:
        return json.dumps({"error": f"No task exists with id {task_id}"}), 404
    return json.dumps(task), 200


@app.route("/tasks/<int:task_id>/", methods=["POST"])
def update_task(task_id):
    body = json.loads(request.data)
    description = body.get("description")
    done = body.get("done")
    DB.update_task_by_id(task_id, description, done)
    task = DB.get_task_by_id(task_id)
    if not task:
        return json.dumps({"error": f"No task exists with id {task_id}"}), 404
    return json.dumps(task), 200
    


@app.route("/tasks/<int:task_id>/", methods=["DELETE"])
def delete_task(task_id):
    task = DB.get_task_by_id(task_id)
    if not task:
        return json.dumps({"error": f"No task exists with id {task_id}"}), 404
    DB.delete_task_by_id(task_id)
    return json.dumps(task), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
