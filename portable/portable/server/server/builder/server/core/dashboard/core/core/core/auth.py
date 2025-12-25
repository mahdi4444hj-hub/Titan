import hashlib

USERS = {
    "admin@local": hashlib.sha256("admin123".encode()).hexdigest()
}

def check(email, password):
    h = hashlib.sha256(password.encode()).hexdigest()
    return USERS.get(email) == h
