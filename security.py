from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

hasher = PasswordHasher()

def hash_password(password):
    hashed_password = hasher.hash(password)
    return hashed_password

def verify_password(hashed_password, password):
    try:
        hasher.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
 