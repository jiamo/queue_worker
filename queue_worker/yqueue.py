import asyncio
import sys
import time
from asyncio import wait_for, wrap_future
from collections import deque
from concurrent.futures import Future
from threading import Condition, Lock, Thread


def from_coroutine():
    return sys._getframe(2).f_code.co_flags & 0x380


def which_pill():
    if from_coroutine():
        print("Red")
    else:
        print("Blue")


def spam():
    which_pill()


async def async_spam():
    which_pill()


# loop.run_until_complete(async_spam())  -> Red


class Queuey:
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.mutex = Lock()
        self.items = deque()
        self.getters = deque()
        self.putters = deque()
        self.all_tasks_done = Condition(self.mutex)
        self.unfinished_tasks = 0

    def get_noblock(self):
        with self.mutex:
            if self.items:
                # Wake a putters
                if self.putters:
                    self.putters.popleft().set_result(True)
                return self.items.popleft(), None
            else:
                fut = Future()
                # 等待输入
                self.getters.append(fut)
                return None, fut

    def put_noblock(self, item):
        with self.mutex:
            if len(self.items) < self.maxsize:
                self.items.append(item)
                self.unfinished_tasks += 1  # putinto
                # Wake a getters
                if self.getters:
                    # 这其实也就是消费了一个
                    self.getters.popleft().set_result(self.items.popleft())
            else:
                fut = Future()
                self.putters.append(fut)
                return fut

    async def get_async(self):
        item, fut = self.get_noblock()
        if fut:
            item = await wait_for(wrap_future(fut), None)
        return item

    def get_sync(self):
        item, fut = self.get_noblock()
        if fut:
            item = fut.result()  # 这个可以获取到 item 为什么不做成不能result 需要在去取呢
        return item

    def get(self):
        if from_coroutine():
            return self.get_async()
        else:
            return self.get_sync()

    async def put_async(self, item):
        while True:
            fut = self.put_noblock(item)
            if fut is None:
                return True
            await wait_for(wrap_future(fut), None)

    def put_sync(self, item):
        while True:
            fut = self.put_noblock(item)
            if fut is None:
                return

            # this is waiting
            fut.result()  # wake and put_noblock again

    def put(self, item):
        if from_coroutine():
            return self.put_async(item)
        else:
            return self.put_sync(item)

    def join(self):
        with self.all_tasks_done:
            while self.unfinished_tasks:
                self.all_tasks_done.wait()

    def task_done(self):
        with self.all_tasks_done:
            unfinished = self.unfinished_tasks - 1
            if unfinished <= 0:
                if unfinished < 0:
                    self.all_tasks_done.notify_all()
                    # raise ValueError('task_done() called too many times')
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished


def producer(q, n):
    for i in range(n):
        q.put(i)
    q.put(None)


def consumer(q):
    while True:
        item = q.get()
        if item is None:
            break
        print("Got:", item)


async def async_consumer(q):
    # loop = asyncio.get_event_loop()
    while True:
        # run a thread in loop or async using q.get_async
        # item = await loop.run_in_executor(None, q.get)
        # This make asyncio.Queue can't work
        item = await q.get()
        if item is None:
            break
        print("Async Got:", item)


async def async_producer(q, n):
    for i in range(n):
        await q.put(i)
    await q.put(None)


if __name__ == "__main__":
    q = Queuey(2)
    Thread(target=producer, args=(q, 10)).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_consumer(q))

    # other
    q = Queuey(2)
    time.sleep(1)
    Thread(target=consumer, args=(q,)).start()
    loop.run_until_complete(async_producer(q, 10))

    time.sleep(1)
    from queue import Queue

    q = Queue()
    Thread(target=producer, args=(q, 10)).start()
    Thread(target=consumer, args=(q,)).start()

    time.sleep(1)
    from asyncio import Queue

    q = Queue()
    loop.create_task(async_consumer(q))
    loop.run_until_complete(async_producer(q, 10))

    time.sleep(1)
