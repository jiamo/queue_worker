from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('queue_worker')
except PackageNotFoundError:
    __version__ = '(local)'
