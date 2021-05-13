from queue import Queue
from .yqueue import Queuey, from_coroutine
from threading import Thread
import traceback
from typing import Callable
import time
from functools import partial
import threading
import inspect
import asyncio
from asyncio import wait_for, wrap_future


class Worker:
    def __init__(self, n: int, queue_maxsize=0, ignore_exceptions=()):
        self.threads = [Thread(target=self._w, daemon=True) for _ in range(n)]
        self.q = Queuey(queue_maxsize)
        self.ignore_exceptions = ignore_exceptions
        for t in self.threads:
            t.start()

    def push_work(self, f: Callable, *args, **kwargs):
        self.q.put((f, args, kwargs))


    def _w(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        threadLocal = threading.local()
        threadLocal.wait_futures = []
        threadLocal.async_tasks = []
        threadLocal.sync_tasks = []

        def handle_item(f_tuple1):
            f1, args1, kwargs1 = f_tuple1
            if inspect.iscoroutinefunction(f1):
                print("hello world", f1, args1, kwargs1)
                task1 = f1(*args1, **kwargs1)
                threadLocal.async_tasks.append(task1)
            else:
                task1 = partial(f1, *args1, **kwargs1)
                threadLocal.sync_tasks.append(task1)


        while True:
            if threadLocal.wait_futures:
                for fut in threadLocal.wait_futures:
                    # need wait TODO how about wait together
                    print("waiting ..... ", fut, self.q.unfinished_tasks)
                    # here need result 
                    # 不在添加也没有等待了
                    # 一个一个结束 可以被 notify
                    f_tuple1 = fut.result()
                    handle_item(f_tuple1)
                # first wait last step waiting future
                threadLocal.wait_futures = []
            for i in range(5):
                f_tuple1, fut1 = self.q.get_noblock()
                if fut1:
                    # print(f_tuple1, fut1, id(fut1), id(loop), self.q.unfinished_tasks)
                    threadLocal.wait_futures.append(fut1)
                else:
                    # print("xxxx ", f_tuple1)
                    handle_item(f_tuple1)
            try:
                # the _w is sync func
                # if from_coroutine():
                task_count = len(threadLocal.async_tasks) + len(threadLocal.sync_tasks)
                if threadLocal.async_tasks:
                    print(threading.get_ident(), "begin async tasks", threadLocal.async_tasks)
                    t = asyncio.gather(*threadLocal.async_tasks)
                    loop.run_until_complete(t)
                    threadLocal.async_tasks = []

                if threadLocal.sync_tasks:
                    for task in threadLocal.sync_tasks:
                        task()
                    threadLocal.sync_tasks = []
                
            except self.ignore_exceptions as e:
                print( e, '...........abort')
            except Exception:
                print('...........error')
                print(traceback.format_exc())
                print('...........error end')
                import _thread
                _thread.interrupt_main()
            finally:
                # 一起减很容易减为 0 
                for i in range(task_count):
                    print("taskdone.........")
                    self.q.task_done()
               

    def join(self):
        self.q.join()


def sleep_print(sleep_time):
    # 只能说这个地方用 异步加速了。
    time.sleep(sleep_time)
    print("----: {} {}".format(threading.get_ident(), sleep_time))
    return

async def async_sleep_print(sleep_time):
    await asyncio.sleep(sleep_time)
    print("----: {} {}".format(threading.get_ident(), sleep_time))
    return


if __name__ == "__main__":
    worker = Worker(16, queue_maxsize=4)
    for i in range(100):
        worker.push_work(partial(async_sleep_print, i%10))
        # 0.11s user 0.08s system 0% cpu 2:01.24 total
        # worker.push_work(partial(async_sleep_print, i%10))
        # 16s
        # python worker.py  0.12s user 0.07s system 2% cpu 9.176 total

    worker.join()