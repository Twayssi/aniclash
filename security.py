from os import getenv
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv

import jwt
from datetime import datetime, timedelta, timezone

load_dotenv()
SECRET_KEY = getenv("SECRET_KEY")
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

def encode_token(user_id, username):
    payload = {'sub': str(user_id), 'username': username, 'exp': datetime.now(timezone.utc) + timedelta(minutes=30.0)}
    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm='HS256')
    return token
    
def decode_token(token):
    payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=['HS256'])
    return payload