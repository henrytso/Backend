import json

from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)


posts = {
    0: {
        "id": 0,
        "upvotes": 6,
        "title": "Look at me! I met a new human today, and he gave me really gentle pets!",
        "link": "https://imgur.com/a/peanut-good-boy-tOslUt0",
        "username": "peanut_goodboy",
        "comments": {}
    },
    1: {
        "id": 1,
        "upvotes": 4,
        "title": "I'm way cuter than any dog... @henreeso #cuteaf",
        "link": "https://imgur.com/a/baby-beibei-o5WzAD2",
        "username": "beibei_meowmeow",
        "comments": {
            0: {
                "id": 0,
                "upvotes": 1,
                "text": "queen bei bei slayyy",
                "username": "beibeifan_xoxo"
            }
        }
    }
}

post_id_counter = 2
comment_id_counter = 1


@app.route("/api/posts/")
def get_posts():
    return jsonify(list(posts.values())), 200


@app.route("/api/posts/", methods=["POST"])
def create_post():
    body = json.loads(request.data)
    title = body.get("title")
    link = body.get("link")
    username = body.get("username")
    if not (title and link and username):
        return jsonify({"error": "Bad Request - Missing required field. Request body requires title, link, and username"}), 400
    global post_id_counter
    post = {
        "id": post_id_counter,
        "upvotes": 0,
        "title": title,
        "link": link,
        "username": username
    }
    posts[post_id_counter] = post
    post_id_counter += 1
    return jsonify(post), 201


@app.route("/api/posts/<int:post_id>/")
def get_post(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": f"No post with id {post_id}."}), 400
    return jsonify(post), 200


@app.route("/api/posts/<int:post_id>/", methods=["DELETE"])
def delete_post(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": f"No post with id {post_id}."}), 400
    del posts[post_id]
    return jsonify(post), 200


@app.route("/api/posts/<int:post_id>/comments/")
def get_comments(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": f"No post with id {post_id}"}), 400
    comments = post.get("comments")
    return jsonify(comments), 200


@app.route("/api/posts/<int:post_id>/comments/", methods=["POST"])
def create_comment(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": f"No post with id {post_id}"}), 400
    body = json.loads(request.data)
    text = body.get("text")
    username = body.get("username")
    if not (text and username):
        return jsonify({"error": "Bad Request - Missing required fields. Request body requires text and username."}), 400
    global comment_id_counter
    comment = {
        "id": comment_id_counter,
        "upvotes": 0,
        "text": text,
        "username": username
    }
    comments = post.get("comments")
    comments[comment_id_counter] = comment
    return jsonify(comment), 201



@app.route("/api/posts/<int:post_id>/comments/<int:comment_id>/", methods=["POST"])
def edit_comment(post_id, comment_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": f"No post with id {post_id}"}), 400
    comments = post.get("comments")
    comment = comments.get(comment_id)
    if not comment:
        return jsonify({"error": f"No comment on post {post_id} with id {comment_id}"}), 400
    body = json.loads(request.data)
    text = body.get("text")
    if not text:
        return jsonify({"error": "Bad Request - Missing required fields. Request body requires text."}), 400
    new_text = body.get("text")
    comment["text"] = new_text
    return jsonify(comment), 200


@app.route("/api/extra/posts/<int:post_id>/", methods=["POST"])
def upvote_post(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": f"No post with id {post_id}"}), 400
    body = json.loads(request.data)
    upvotes = 1 if not body.get("upvotes") else body.get("upvotes")
    post["upvotes"] += upvotes
    return jsonify(post), 200


@app.route("/api/extra/posts/")
def get_posts_sorted():
    url_parameters = request.args
    sort = url_parameters.get("sort")
    decreasing = url_parameters.get("sort") == "decreasing"
    print(f"sort = {sort}")
    print(f"type is {type(sort)}")
    print(f"decreasing = {decreasing}")
    sorted_posts = sorted(posts.values(), key=lambda p: p["upvotes"], reverse=decreasing)
    return jsonify(sorted_posts), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
