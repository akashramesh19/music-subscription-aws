from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
from boto3.dynamodb.conditions import Key

app = Flask(__name__)
CORS(app)

REGION = os.getenv("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)

login_table = dynamodb.Table(os.getenv("LOGIN_TABLE", "login"))
music_table = dynamodb.Table(os.getenv("MUSIC_TABLE", "music"))
subscriptions_table = dynamodb.Table(os.getenv("SUBSCRIPTIONS_TABLE", "subscriptions"))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    email = data.get("email")
    user_name = data.get("user_name")
    password = data.get("password")

    if not email or not user_name or not password:
        return jsonify({"message": "Email, username and password are required"}), 400

    existing_user = login_table.get_item(Key={"email": email})

    if "Item" in existing_user:
        return jsonify({"message": "The email already exists"}), 409

    login_table.put_item(
        Item={
            "email": email,
            "user_name": user_name,
            "password": password
        }
    )

    return jsonify({
        "message": "User registered successfully",
        "email": email,
        "user_name": user_name
    }), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    response = login_table.get_item(Key={"email": email})
    user = response.get("Item")

    if not user or user.get("password") != password:
        return jsonify({"message": "email or password is invalid"}), 401

    return jsonify({
        "message": "Login successful",
        "email": user["email"],
        "user_name": user.get("user_name", "")
    }), 200


@app.route("/music", methods=["GET"])
def get_music():
    artist = request.args.get("artist", "").strip()
    title  = request.args.get("title",  "").strip().lower()
    year   = request.args.get("year",   "").strip()
    album  = request.args.get("album",  "").strip().lower()

    try:
        if artist and year:
            # LSI: artist-year-lsi — exact year match on artist partition
            result = music_table.query(
                IndexName="artist-year-lsi",
                KeyConditionExpression=Key("artist").eq(artist) & Key("year").eq(year)
            )
            songs = result.get("Items", [])
        elif artist:
            # Base table Query on partition key
            result = music_table.query(
                KeyConditionExpression=Key("artist").eq(artist)
            )
            songs = result.get("Items", [])
        elif year:
            # GSI: year-index — all songs from a given year without full Scan
            result = music_table.query(
                IndexName="year-index",
                KeyConditionExpression=Key("year").eq(year)
            )
            songs = result.get("Items", [])
        else:
            # No key available — full Scan with pagination
            result = music_table.scan()
            songs  = result.get("Items", [])
            while "LastEvaluatedKey" in result:
                result = music_table.scan(ExclusiveStartKey=result["LastEvaluatedKey"])
                songs.extend(result.get("Items", []))

        # In-memory filter for non-key attributes (title, album)
        if title:
            songs = [s for s in songs if title in s.get("title", "").lower()]
        if album:
            songs = [s for s in songs if album in s.get("album", "").lower()]

        return jsonify({"songs": songs}), 200

    except Exception as e:
        return jsonify({"message": "Error retrieving music", "error": str(e)}), 500


@app.route("/subscriptions", methods=["GET"])
def get_subscriptions():
    email = request.args.get("email")

    if not email:
        return jsonify({"message": "Email is required"}), 400

    try:
        response = subscriptions_table.query(
            KeyConditionExpression=Key("email").eq(email)
        )

        subscriptions = response.get("Items", [])

        return jsonify({"subscriptions": subscriptions}), 200

    except Exception as e:
        return jsonify({
            "message": "Error retrieving subscriptions",
            "error": str(e)
        }), 500


@app.route("/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json() or {}

    email = data.get("email")
    title = data.get("title")
    album = data.get("album")
    artist = data.get("artist")
    year = data.get("year")
    image_url = data.get("image_url", "")

    if not email or not title or not album:
        return jsonify({"message": "Email, title and album are required"}), 400

    title_album_key = f"{title}#{album}"

    try:
        subscriptions_table.put_item(
            Item={
                "email": email,
                "title#album": title_album_key,
                "title": title,
                "album": album,
                "artist": artist,
                "year": str(year),
                "image_url": image_url
            }
        )

        return jsonify({"message": "Subscription added successfully"}), 201

    except Exception as e:
        return jsonify({
            "message": "Error adding subscription",
            "error": str(e)
        }), 500


@app.route("/unsubscribe", methods=["DELETE"])
def unsubscribe():
    data = request.get_json() or {}

    email = data.get("email")
    title = data.get("title")
    album = data.get("album")

    if not email or not title or not album:
        return jsonify({"message": "Email, title and album are required"}), 400

    title_album_key = f"{title}#{album}"

    try:
        subscriptions_table.delete_item(
            Key={
                "email": email,
                "title#album": title_album_key
            }
        )

        return jsonify({"message": "Subscription removed successfully"}), 200

    except Exception as e:
        return jsonify({
            "message": "Error removing subscription",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)