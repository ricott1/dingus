import os
import time

def test_hashing(capsys):
    start_time = time.time()
    data = [os.urandom(1500) for _ in range(20000)]
    with capsys.disabled():
        print(f"\ndata: {time.time() - start_time:.2f}s")

    for d in data:
        hash(d)
    with capsys.disabled():
        print(f"\nhashing: {time.time() - start_time:.2f}s")