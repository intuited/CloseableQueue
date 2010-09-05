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
        Queue.__init__(*args, **kwargs)
        from Queue import threading

    def close(now=False):
        """Marks the queue closed.

        If `now` is True, the queue is marked as immediately closed
          and any further `get`s will raise Empty exceptions for the consumer
          and Full exceptions for the producer.

        If `now` is False, no further contents will be accepted.
        `put` attempts will raise Full exceptions;
          `get`s will work normally until the current contents are exhausted.
        Once the queue is empty,
          Empty exceptions will be raised unconditionally on `get`.

        The close method may usefully be called
          by a sole consumer or by a sole producer.

        When called by the sole consumer, it indicates immediately to producers
          that they should stop producing.
        This will normally be done with now=True.

        When called by the sole producer, normally with now=False,
          it indicates that production has stopped, and consumers should cease.

        Additionally, any currently blocked `get`s or `put`s will be unblocked,
          and will raise Closed exceptions.

        Use by one of a number of producers or consumers
          is not normally meaningful.
        """
        pass

    def closing(now=False):
        """Returns a context manager which calls `close` on the queue.

        This allows code like
            >>> with CloseableQueue().closing(True) as q:
            ...     producers = [Thread(target=produce, args=(q,)).start()
            ...                  for i in range(4)]
            ...     while True:
            ...         consumed = q.get()
            ...         if consumed == ohnoes:
            ...             raise OhNoesError('Oh Noes!  The value {0} was produced!'
            ...                               .format(consumed))

        to properly close the queue from the consumer end.
        """
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
