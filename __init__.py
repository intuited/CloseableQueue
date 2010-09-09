"""Defines the CloseableQueue class.

This class provides a means to permanently close a queue.

Attempts to `put` to a closed queue will raise the `Closed` exception.

Attempts to `get` from an *empty* closed queue will raise the same.

Blocked `put`s and `get`s on a queue which is subsequently closed
  will also raise the `Closed` exception under the same circumstances.

A queue can be closed either by calling its `close` method
  or by passing `last=True` to an invocation of `put`.

If the latter is done, the entire operation is performed atomically;
  the close will only take place if the put succeeds.
"""
from Queue import Queue, Empty, Full, _time

class Closed(Exception):
    """Exception raised by CloseableQueue.put/get on a closed queue."""
    pass

class CloseableQueue(Queue):
    def __init__(self, *args, **kwargs):
        Queue.__init__(self, *args, **kwargs)
        assert not hasattr(self, '_closed')
        self._closed = False

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
        self.mutex.acquire()
        try:
            if not self._closed:
                self._closed = True
                self.not_empty.notify_all()
                self.not_full.notify_all()
        finally:
            self.mutex.release()

    def closed(self):
        """True iff the queue is closed.  Unreliable like `empty` and `full`."""
        # Probably not necessary to use a protected section here,
        #   but better safe than bug-ridden.
        # This also leaves the door open
        #   for more complex implementations of `_closed` as a property.
        self.mutex.acquire()
        n = self._closed
        self.mutex.release()
        return n

    def put(self, item, block=True, timeout=None, last=False):
        """Put an item into the queue.

        Works as does `Queue.Queue.put`, but with these differences:

        If the queue is closed, raises Closed.

        If `last` is True and the put succeeds,
          the queue will be atomically closed.

        Also raises `Closed` in the event that the queue is closed
          while the `put` is blocked.
        """
        self.not_full.acquire()
        try:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() == self.maxsize and not self._closed:
                        raise Full
                elif timeout is None:
                    while self._qsize() == self.maxsize and not self._closed:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                else:
                    endtime = _time() + timeout
                    while self._qsize() == self.maxsize and not self._closed:
                        remaining = endtime - _time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            if self._closed:
                raise Closed
            self._put(item)
            self.unfinished_tasks += 1
            if last:
                self._closed = True
                self.not_empty.notify_all()
                self.not_full.notify_all()
            else:
                self.not_empty.notify()
        finally:
            self.not_full.release()

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        Works as does `Queue.Queue.get` except that
          a `get` on a closed queue will raise `Closed`.

        Similarly, a blocked `get` will raise `Closed`
          if the queue is closed during the block.
        """
        self.not_empty.acquire()
        try:
            if not block:
                if not self._qsize() and not self._closed:
                    raise Empty
            elif timeout is None:
                while not self._qsize() and not self._closed:
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a positive number")
            else:
                endtime = _time() + timeout
                while not self._qsize() and not self._closed:
                    remaining = endtime - _time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            if self._closed and not self._qsize():
                raise Closed
            item = self._get()
            self.not_full.notify()
            return item
        finally:
            self.not_empty.release()
