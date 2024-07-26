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


@app.route("/api/transactions/", methods=["POST"])
def create_transaction():
    body = json.loads(request.data)
    sender_id = body.get("sender_id")
    receiver_id = body.get("receiver_id")
    amount = body.get("amount")
    message = body.get("message")
    accepted = body.get("accepted")
    if (sender_id and receiver_id and amount and message) is None:
        return failure_response("Bad request - body requires fields: sender_id, receiver_id, amount, message.", code=400)
    if accepted is False:
        return failure_response("Cannot create new transaction that is rejected.", code=403)
    sender = DB.get_user_by_id(sender_id)
    if not sender:
        return failure_response(f"No user with id {sender_id}")
    if amount <= 0:
        return failure_response(f"Please enter a valid amount.", code=400)
    if accepted and amount > sender["balance"]:
        return failure_response(f"Sender {sender_id} has insufficient funds.", code=400)
    receiver = DB.get_user_by_id(receiver_id)
    if not receiver:
        return failure_response(f"No user with id {receiver_id}")
    txn_id = DB.insert_txn_table(sender_id, receiver_id, amount, message, accepted)
    txn = DB.get_txn_by_id(txn_id)
    if not txn:
        return failure_response("Txn not created.", code=500)
    return success_response(txn, code=201)


@app.route("/api/transactions/<int:transaction_id>/", methods=["POST"])
def accept_or_deny_transaction(transaction_id):
    body = json.loads(request.data)
    accepted = body.get("accepted")
    if accepted is None:
        return failure_response(f"Bad request - required field: accepted.", code=400)
    transaction = DB.get_txn_by_id(transaction_id)
    if not transaction:
        return failure_response(f"No transaction with id {transaction_id}.")
    if transaction["accepted"] is not None:
        return failure_response(f"Transaction with id {transaction_id} has already been settled as {'accepted' if transaction['accepted'] else 'rejected'}.", code=403)
    txn = DB.get_txn_by_id(transaction_id)
    sender = DB.get_user_by_id(txn["sender_id"])
    if accepted and txn["amount"] > sender["balance"]:
        return failure_response(f"Sender with id {sender['id']} has insufficient funds.", code=403)
    updated_txn = DB.update_txn(transaction_id, accepted)
    if not updated_txn:
        return failure_response(f"Database could not update transaction with id {transaction_id}.", code=500)
    return success_response(updated_txn, code=200)


@app.route("/api/extra/users/<int:user_id>/join/")
def get_transactions_of_user(user_id):
    user = DB.get_user_by_id(user_id)
    if not user:
        return failure_response(f"No user with id {user_id}.")
    txns = DB.get_txns_of_user_join(user_id)
    return success_response(txns)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
