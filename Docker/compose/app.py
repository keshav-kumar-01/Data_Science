import time
import redis
from flask import Flask

app = Flask(__name__)

cache = redis.Redis(
    host='redis',   # ← MUST be service name
    port=6379,
    decode_responses=True
)

def get_hit_count():
    retries = 5
    while True:
        try:
            return cache.incr('hits')
        except redis.exceptions.ConnectionError:
            if retries == 0:
                raise
            retries -= 1
            time.sleep(0.5)

@app.route('/')
def hello():
    count = get_hit_count()
    return f'Keshav, I have seen you {count} times\n'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
