from flask import Flask, request, jsonify
import requests
import os
import json
import time

SECRET_KEY = os.environ.get("SECRET_KEY", "")
ROBLOX_API_KEY = os.environ.get("ROBLOX_API_KEY", "")
UNIVERSE_ID = os.environ.get("UNIVERSE_ID", "")
DATASTORE_NAME = "PlayerGiveGamePasses_v1"

app = Flask(__name__)

ROBLOX_USER_API = "https://users.roblox.com/v1/usernames/users"

def get_roblox_id(username):
    try:
        resp = requests.post(
            ROBLOX_USER_API,
            json={"usernames": [username], "excludeBannedUsers": True},
            timeout=5
        )
        users = resp.json().get("data", [])
        return users[0]["id"] if users else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def set_datastore(user_id, value):
    url = f"https://apis.roblox.com/datastores/v1/universes/{UNIVERSE_ID}/standard-datastores/datastore/entries/entry"
    params = {"datastoreName": DATASTORE_NAME, "entryKey": f"givenpass_{user_id}"}
    headers = {"x-api-key": ROBLOX_API_KEY, "content-type": "application/json"}
    return requests.post(url, params=params, headers=headers, data=json.dumps(value), timeout=10)

def get_datastore(user_id):
    url = f"https://apis.roblox.com/datastores/v1/universes/{UNIVERSE_ID}/standard-datastores/datastore/entries/entry"
    params = {"datastoreName": DATASTORE_NAME, "entryKey": f"givenpass_{user_id}"}
    headers = {"x-api-key": ROBLOX_API_KEY}
    return requests.get(url, params=params, headers=headers, timeout=10)

@app.route("/give-vvip", methods=["POST"])
def give_vvip():
    data = request.get_json()

    if data.get("secret") != SECRET_KEY:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    username = data.get("username", "").strip()
    if not username:
        return jsonify({"success": False, "error": "Username kosong"}), 400

    roblox_id = get_roblox_id(username)
    if not roblox_id:
        return jsonify({"success": False, "error": f"Username '{username}' tidak ditemukan"}), 404

    vvip_data = {
        "passType": "VVIP",
        "givenBy": 0,
        "givenAt": int(time.time()),
        "timestamp": time.time(),
        "note": f"Given via Discord by {data.get('given_by', 'Bot')}"
    }

    resp = set_datastore(roblox_id, vvip_data)

    if resp.status_code in (200, 201):
        return jsonify({"success": True, "roblox_id": roblox_id, "username": username})

    return jsonify({"success": False, "error": f"DataStore error: {resp.status_code}"}), 500


# 🔥 TAMBAHAN INI
@app.route("/check-vvip/<username>", methods=["GET"])
def check_vvip(username):
    roblox_id = get_roblox_id(username)
    if not roblox_id:
        return jsonify({"success": False, "error": "Username tidak ditemukan"}), 404

    resp = get_datastore(roblox_id)

    if resp.status_code == 200:
        entry = resp.json()
        is_vvip = entry.get("passType") == "VVIP"
        return jsonify({"success": True, "is_vvip": is_vvip, "roblox_id": roblox_id})

    if resp.status_code == 404:
        return jsonify({"success": True, "is_vvip": False, "roblox_id": roblox_id})

    return jsonify({"success": False, "error": f"DataStore error: {resp.status_code}"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
