import json
import os
import hashlib

USERS_FILE = "users.json"


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    with open(USERS_FILE, "r") as file:
        return json.load(file)


def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump(users, file, indent=2)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password):
    users = load_users()

    if username in users:
        return False

    users[username] = {
        "password": hash_password(password)
    }

    save_users(users)

    return True


def authenticate(username, password):
    users = load_users()

    if username not in users:
        return False

    return users[username]["password"] == hash_password(password)