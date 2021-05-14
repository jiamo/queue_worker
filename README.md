# Overview

queue worker for sync and async function

[![Unix Build Status](https://img.shields.io/travis/com/jiamo/queue_worker.svg?label=unix)](https://travis-ci.com/jiamo/queue_worker)
[![PyPI Version](https://img.shields.io/pypi/v/queue_worker.svg)](https://pypi.org/project/queue_worker)
[![PyPI License](https://img.shields.io/pypi/l/queue_worker.svg)](https://pypi.org/project/queue_worker)

# Setup

## Requirements

* Python 3.8+

## Installation

Install it directly into an activated virtual environment:

```text
$ pip install queue_worker
```

or add it to your [Poetry](https://poetry.eustace.io/) project:

```text
$ poetry add queue_worker
```

# Usage

After installation, the package can imported:

```text

async def async_sleep_print(sleep_time):
    await asyncio.sleep(sleep_time)
    print("----: {} {}".format(threading.get_ident(), sleep_time))
    return


if __name__ == "__main__":
    worker = Worker(16, queue_maxsize=4)
    for i in range(100):
        worker.push_work(partial(async_sleep_print, i%10))
    worker.join()
```
