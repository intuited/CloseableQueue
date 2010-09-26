"""Defines the CloseableQueue class and the Close exception class."""

from Queue import Empty, Full, _time
import Queue as _Queue

class Closed(Exception):
    """Exception raised by CloseableQueue.put/get on a closed queue."""
    pass

def CloseableQueueFactory(base=_Queue.Queue, name="CloseableQueue"):
    """Create a closeable descendant class of `base`.

    Used instead of a mixin approach because the Queue module's classes
      are old-style.
    """
    class CloseableQueue(base):
        """This class provides a means to permanently close a queue.

        Attempts to `put` to a closed queue will raise the `Closed` exception.

        Attempts to `get` from an *empty* closed queue will raise the same.

        Blocked `put`s and `get`s on a queue which is subsequently closed
          will also raise the `Closed` exception under the same circumstances.

        A queue can be closed either by calling its `close` method
          or by passing `last=True` to an invocation of `put`.

        If the latter is done, the entire operation is performed atomically;
          the close will only take place if the put succeeds.
        """
        def __init__(self, *args, **kwargs):
            base.__init__(self, *args, **kwargs)
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
    CloseableQueue.__name__ = name
    return CloseableQueue

CloseableQueue = CloseableQueueFactory()
CloseableLifoQueue = CloseableQueueFactory(_Queue.LifoQueue,
                                           "CloseableLifoQueue")
CloseablePriorityQueue = CloseableQueueFactory(_Queue.PriorityQueue,
                                               "CloseablePriorityQueue")

def dequeue(q, getargs={}, on_empty='stop'):
    """Generates values from the queue `q`.

    This is a fairly flexible function which can also be meaningfully applied
      to non-closeable queues, by passing a `timeout` in `getargs`.

    The default arguments are suitable for generating an iteration
      from a queue which is closed after/as the last value is `put` to it.

    To avoid false StopIterations, if a timeout is used with a closeable queue,
      `on_empty` should be passed as `raise` or some sentinel value.

    `getargs` is a dict which will comprise the keyword arguments to `q.get`.

    `on_empty` determines the response to an `Empty` exception raised by `get`.
      If 'raise', the `Empty` exception will be raised.
      If 'stop', the `Empty` exception will be treated as a `Closed` exception.
      Otherwise, the value passed in `on_empty` will be yielded.

    Note that with the default value of `getargs`,
      `Empty` exceptions will not occur.
    """
    try:
        while True:
            yield q.get(**getargs)
    except Closed:
        raise StopIteration
    except Empty:
        if on_empty == 'raise':
            raise
        elif on_empty == 'stop':
            raise StopIteration
        else:
            yield on_empty

def enqueue(it, q, putargs={}, join=False, close=True):
    """`put`s the successive values of the iterable `it` into `q`.

    The default values will close the queue after the final iterated value.

    `putargs` is a dict which will comprise the keyword arguments to `q.put`.

    If `close` is true,
      `q` must support the `close` method, i.e. be a CloseableQueue.
    This will have the effect of closing the queue after the end of iteration.

    If `join` is true, the queue is joined after the values are put,
      and after optionally being closed.
    """
    for value in iter(it):
        q.put(value, **putargs)
    if close:
        q.close()
    if join:
        q.join()

def EnqueueThread(it, q=None, name='enqueue', start=True, enqueue=enqueue,
                  **kwargs):
    """Starts a thread which enqueues the values of the iterable `it`.

    If a queue is not passed, a new one is created.

    A reference to the queue is stored as the property `q`
      of the returned thread.

    The thread will be started unless `start` is false.

    This is ideal for processing generators
      and other iterables which lazily process I/O-bound operations.

    Passing the return value of a `dequeue` call will have the effect
      of creating a processing thread which pulls from and pushes to
      thread-safe data structures.

    Additional keyword arguments are passed on to `enqueue`.
    """
    from threading import Thread
    if q is None:
        q = CloseableQueue()
    thread = Thread(name=name,
                    target=enqueue,
                    args=(it, q),
                    kwargs=kwargs)
    thread.q = q
    if start:
        thread.start()
    return thread
