"""Tests for the CloseableQueue class.

These tests build on the unit tests provided for the Queue module.

That module's test code should be included in the file `test_queue.py`.
"""
from test_queue import BlockingTestMixin, BaseQueueTest
from test_queue import FailingQueue, FailingQueueTest
from CloseableQueue import CloseableQueue, Closed
import unittest

# Because the method queue_test.BaseQueueTest.simple_queue_test
#   uses the queue class name,
#   it has to be the name of one of the Queue classes.
# In order to avoid Heisenbugs, we don't create new classes;
#   we just rename the existing ones during the test.
def base_queue_class_name(cls):
    cls_name = cls.__name__
    return cls_name[cls_name.index('able') + 4:]

class RenamingBaseQueueTest(BaseQueueTest):
    def setUp(self):
        self._old_typename = self.type2test.__name__
        self.type2test.__name__ = base_queue_class_name(self.type2test)
        super(RenamingBaseQueueTest, self).setUp()

    def tearDown(self):
        super(RenamingBaseQueueTest, self).tearDown()
        self.type2test.__name__ = self._old_typename


class RegressionCloseableQueueTest(RenamingBaseQueueTest):
    type2test = CloseableQueue


class FailingCloseableQueue(CloseableQueue):
    def __init__(self, *args):
        self.fail_next_put = False
        self.fail_next_get = False
        CloseableQueue.__init__(self, *args)
    def _put(self, item):
        if self.fail_next_put:
            self.fail_next_put = False
            raise FailingQueueException, "You Lose"
        return CloseableQueue._put(self, item)
    def _get(self):
        if self.fail_next_get:
            self.fail_next_get = False
            raise FailingQueueException, "You Lose"
        return CloseableQueue._get(self)

class FailingCloseableQueueTest(FailingQueueTest):
    def test_failing_queue(self):
        # Test to make sure a queue is functioning correctly.
        # Done twice to the same instance.
        q = FailingCloseableQueue(QUEUE_SIZE)
        self.failing_queue_test(q)
        self.failing_queue_test(q)


def put_iterable(q, it, putargs={}, close=-1, last=-1):
    """Puts the iterable to the queue `q`.

    `last` and `close`, as positive integers,
        indicate the number of puts before, respectively,
        the `last` parameter is passed to `put`
        or a `close` is called after `put`.
    """
    for i in iter(it):
        ret = q.put(i, last=last==0, **putargs)
        if close == 0:
            q.close(*closeargs)
        close -= 1
        last -= 1
    return ret
def get_iterable(q, getargs={}, count=-1):
    while True:
        if count == 0:
            break
        yield q.get(**getargs)
        count -= 1
def get_tuple(q, getargs={}, count=-1):
    return tuple(get_iterable(q, getargs, count))

class CloseableQueueTest(unittest.TestCase, BlockingTestMixin):
    type2test = CloseableQueue

    def setUp(self):
        # set up cumulative counts for `test_join_after_close`
        import threading
        self.cum = 0
        self.cumlock = threading.Lock()

    def test_take_until_before_last(self):
        """Close the queue with `last` and then get its stored values."""
        q = self.type2test()
        # To ensure that the last is actually put before we start the get,
        #   we do this manually, without threads.
        q.put(1)
        q.put(2)
        q.put(3, last=True)
        result = get_tuple(q, {'block': False}, 3)
        self.assertEqual((1, 2, 3), result)

    def test_take_until_after_last(self):
        """`Get` after a last `put`.
        
        Since the second `get` doesn't block, this should verify
           (as well as possible) that
          `put(last=True)` closes the queue atomically.

        In practice this is mostly useful as a regression test, since
          it's pretty obvious by reading `put` that it's working atomically.
        """
        def get_then_get(q):
            """Serves to verify the atomicity of `put(last=True)`."""
            q.get(timeout=2)
            q.get(block=False)

        q = self.type2test()
        try:
            self.do_exceptional_blocking_test(get_then_get, (q,),
                                              q.put, (1, False, None, True),
                                              Closed)
        except Closed:
            pass
        else:
            self.fail('Closed exception not raised.')

    def test_put_after_last(self):
        q = self.type2test()
        q.put(1, last=True)
        try:
            q.put(2)
        except Closed:
            pass
        else:
            self.fail('Closed exception not raised.')

    def test_get_after_close_on_empty_queue(self):
        """Test that `get` calls made after a `close` raise `Closed`."""
        q = self.type2test()
        q.close()
        try:
            q.get(timeout=0.1)
        except Closed:
            pass
        else:
            self.fail('Closed exception not raised.')

    def test_get_after_close_on_nonempty_queue(self):
        q = self.type2test()
        q.put(1)
        q.close()
        self.assertEqual(1, q.get(block=False))

    def test_put_after_close(self):
        q = self.type2test()
        q.close()
        try:
            q.put(1, timeout=0.1)
        except Closed:
            pass
        else:
            self.fail('Closed exception not raised.')

    def test_close_after_get_on_empty_queue(self):
        """Test that calling `close` raises `Closed` in a blocked thread."""
        q = self.type2test()
        try:
            self.do_exceptional_blocking_test(q.get, (True, 2), q.close, (),
                                              Closed)
        except Closed:
            pass
        else:
            self.fail('Closed exception not raised.')

    def test_close_after_put_on_full_queue(self):
        """This should also cause a release with a `Closed` exception."""
        q = self.type2test(1)
        q.put(1)
        try:
            self.do_exceptional_blocking_test(q.put, (2, True, 0.4),
                                              q.close, (), Closed)
        except Closed:
            pass
        else:
            self.fail('Closed exception not raised.')

    def worker(self, q):
        """Worker based on `test_queue.BaseQueueTest.worker`.

        Only used for `test_join_after_close`.
        """
        try:
            while True:
                x = q.get()
                if x is None:
                    q.task_done()
                    return
                with self.cumlock:
                    self.cum += x
                q.task_done()
        except Closed:
            pass

    def test_join_after_close(self):
        """Based on `test_queue.BaseQueueTest.queue_join_test`."""
        import threading
        q = self.type2test()
        self.cum = 0
        for i in (0,1):
            threading.Thread(target=self.worker, args=(q,)).start()
        for i in xrange(100):
            q.put(i)
        q.close()
        q.join()
        self.assertEquals(self.cum, sum(range(100)),
                          "q.join() did not block until all tasks were done")
        try:
            for i in (0,1):
                q.put(None)         # instruct the threads to close
        except Closed:
            pass
        else:
            self.fail('Closed exception not raised.')
        q.join()                # verify that you can join twice
        try:
            q.task_done()
        except ValueError:
            pass
        else:
            self.fail("Did not detect task count going negative")


class QueueIterationTest(unittest.TestCase, BlockingTestMixin):
    """Tests the `enqueue` and `dequeue` functions."""
    def do_iterable_test(self, it, q=None,
                         getargs={'timeout': 0.2}, putargs={'timeout': 0.2},
                         on_empty='raise', join=False, close=True):
        """Verifies that the iterable is the same after being en/dequeued."""
        from CloseableQueue import enqueue, dequeue, CloseableQueue
        if q is None:
            q = CloseableQueue()
        tup = tuple(it)
        def dequeue_to_tuple():
            return tuple(dequeue(q, getargs, on_empty))
        result = self.do_blocking_test(dequeue_to_tuple, (),
                                       enqueue, (it, q, putargs, join, close))
        self.assertEqual(tup, tuple(result))
        if close:
            try:
                q.get(timeout=0.2)
            except Closed:
                pass
            else:
                self.fail('Closed exception not raised.')
        return result
        
    def test_empty_iterable(self):
        self.do_iterable_test(())

    def test_nonempty_iterable(self):
        self.do_iterable_test((1, 2, 3))

    def test_timeout_iterable(self):
        q = CloseableQueue()
        self.do_iterable_test((1, 2, 3), q, on_empty='stop', close=False)
        self.do_iterable_test((4, 5, 6), q, on_empty='stop', close=False)
        self.do_iterable_test((7, 8, 9), q, on_empty='stop', close=True)

def make_test_suite():
    from unittest import TestSuite, defaultTestLoader
    load = defaultTestLoader.loadTestsFromTestCase
    testcases = (RegressionCloseableQueueTest, FailingCloseableQueue,
                 CloseableQueueTest, QueueIterationTest)
    return TestSuite(load(case) for case in testcases)

def test_main():
    from unittest import TextTestRunner
    TextTestRunner().run(make_test_suite())

if __name__ == "__main__":
    test_main()
