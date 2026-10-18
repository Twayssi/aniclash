import redis
from dotenv import load_dotenv
from os import getenv


load_dotenv()
client = redis.Redis(host=getenv('REDIS_HOST'), port=int(getenv('REDIS_PORT')), decode_responses=True, password=getenv('REDIS_PASSWORD') or None)