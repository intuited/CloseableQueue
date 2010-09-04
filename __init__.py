"""Defines the CloseableQueue and IterableQueue classes.

These are subclasses of the Queue class, and implement the close() method
  and derived functionality.
"""
from Queue import Queue, Empty, Full, _time

class CloseableQueue(Queue):
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

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a positive number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
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

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a positive number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).
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
