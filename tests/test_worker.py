import asyncio
import threading
from functools import partial

from queue_worker.worker import Worker


total = 0


async def add(sleep_time):
    global total
    await asyncio.sleep(sleep_time % 4)
    print("----: {} {}".format(threading.get_ident(), sleep_time))
    total += sleep_time
    return


def test_worker():
    worker = Worker(16, queue_maxsize=4)
    for i in range(1, 21):
        worker.push_work(partial(add, i))
    worker.join()
    print("total ", total)
    assert total == 210
