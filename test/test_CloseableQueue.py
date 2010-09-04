"""Tests for the CloseableQueue class.

These tests build on the unit tests provided for the Queue module.

That module's test code should be included in the file `test_queue.py`.
"""
from test_queue import BaseQueueTest, FailingQueue, FailingQueueTest
from CloseableQueue import CloseableQueue
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


def make_test_suite():
    from unittest import TestSuite, defaultTestLoader
    load = defaultTestLoader.loadTestsFromTestCase
    testcases = (RegressionCloseableQueueTest, FailingCloseableQueue)
    return TestSuite(load(case) for case in testcases)

def test_main():
    from unittest import TextTestRunner
    TextTestRunner().run(make_test_suite())

if __name__ == "__main__":
    test_main()
