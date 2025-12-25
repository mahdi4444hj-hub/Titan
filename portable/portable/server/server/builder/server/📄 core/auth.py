import hashlib

USERS = {
    "admin@example.com": hashlib.sha256("123456".encode()).hexdigest()
}

def verify_user(email, password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return USERS.get(email) == hashed
