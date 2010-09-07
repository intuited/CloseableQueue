"""Defines the CloseableQueue and IterableQueue classes.

These are subclasses of the Queue class, and implement the close() method
  and derived functionality.
"""
from Queue import Queue, Empty, Full, _time

class Closed(Exception):
    """Exception raised by CloseableQueue.put/get on a closed queue."""
    pass

class CloseableQueue(Queue):
    def __init__(self, *args, **kwargs):
        Queue.__init__(self, *args, **kwargs)

    def close(self):
        """Close the queue.

        This will prevent further `put`s, and only allow `get`s
          until the contents are depleted.

        `put`s and `get`s which are prevented raise `Closed`.

        Calling `close` will also cause `Closed` exceptions to be raised
          in blocked `get`s or `put`s as though they had just been called.

        Normally it is only useful to call this method
          from a thread which is the sole producer or sole consumer.
        """
        pass

    def closing(self):
        """Returns a context manager which calls `close` on the queue."""
        pass

    def put(self, item, block=True, timeout=None, last=False):
        """Put an item into the queue.

        Works as `Queue.Queue.put` but with these differences:

        If the queue is closed, raises Closed.

        If `last` is True, the item being put, if successfully put,
          will mark the end of the Queue.  When a consumer `get`s that item,
          the queue will be marked closed.
        """
        self.not_full.acquire()
        try:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() == self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() == self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                else:
                    endtime = _time() + timeout
                    while self._qsize() == self.maxsize:
                        remaining = endtime - _time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()
        finally:
            self.not_full.release()

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        Works as does `Queue.Queue.get` except that
          a `get` on a closed queue will raise Closed.
        """
        self.not_empty.acquire()
        try:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a positive number")
            else:
                endtime = _time() + timeout
                while not self._qsize():
                    remaining = endtime - _time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self._get()
            self.not_full.notify()
            return item
        finally:
            self.not_empty.release()
