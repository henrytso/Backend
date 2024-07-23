import json
from flask import Flask, request
import db

DB = db.DatabaseDriver()

app = Flask(__name__)


def success_response(body, code=200):
    return json.dumps(body), code

def failure_response(message, code=404):
    return json.dumps({"error": message}), code


@app.route("/api/users/")
def get_users():
    return success_response(DB.get_all_users())


@app.route("/api/users/", methods=["POST"])
def create_user():
    body = json.loads(request.data)
    name = body.get("name")
    username = body.get("username")
    if not (name and username):
        return failure_response("Bad request - body requires fields: name, username.", code=400)
    balance = body.get("balance") if body.get("balance") else 0
    user_id = DB.insert_user_table(name, username, balance)
    if not user_id:
        return failure_response("User not created.", code=500)
    return success_response(DB.get_user_by_id(user_id), code=201)


@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    user = DB.get_user_by_id(user_id)
    if not user:
        return failure_response(f"No user with id {user_id} found.")
    return success_response(user)


@app.route("/api/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    user = DB.get_user_by_id(user_id)
    if not user:
        return failure_response(f"No user with id {user_id}")
    DB.delete_user_by_id(user_id)
    return success_response(user, code=202)


@app.route("/api/send/", methods=["POST"])
def send_money():
    body = json.loads(request.data)
    sender_id = body.get("sender_id")
    receiver_id = body.get("receiver_id")
    amount = body.get("amount")
    if (sender_id and receiver_id and amount) is None:
        return failure_response("Bad request - body requires fields: sender_id, receiver_id, amount.", code=400)
    sender = DB.get_user_by_id(sender_id)
    if not sender:
        return failure_response(f"No user with id {sender_id}")
    receiver = DB.get_user_by_id(receiver_id)
    if not receiver:
        return failure_response(f"No user with id {receiver_id}")
    if amount > sender["balance"]:
        return failure_response(f"Sender {sender['name']} has insufficent funds.", code=400)
    DB.transfer_user_balance(sender_id, receiver_id, amount)
    return success_response(body)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
