``CloseableQueue``
==================

The ``CloseableQueue`` module includes the ``Closeable*Queue`` classes
as well as the ``Closed`` exception and some utility functions.

These classes and functions provide the facility to close a queue
and to use it as an iterator.


The ``Closeable*Queue`` classes
-------------------------------

The ``CloseableQueue`` class adds to ``Queue.Queue``
the means to permanently close a queue.

This is intended to provide queue support for functionality
that would otherwise be implemented through the use of sentinel values
or other mechanisms.
Such workarounds can be particularly awkward
in the case of multi-consumer queues.

``CloseableQueue`` class provides both a ``close`` method
and an extra parameter, ``last``, to its ``put`` method.

``CloseableLifoQueue`` and ``CloseablePriorityQueue`` are similar classes
which subclass Queue.LifoQueue and Queue.PriorityQueue respectively.

Further details are available in the docstrings of the classes
and their methods.


``CloseableQueueFactory``
-----------------------

This factory function is used to create the ``Closeable*Queue`` classes.

This approach is used instead of a mixin class
because the Queue module's classes are old-style.

It should be possible to apply this function to other ``Queue``-derived classes,
as long as they have not overridden ``get`` or ``put``
(or defined ``close`` or ``closed``).

For example:

::

    >>> CloseableFooQueue = CloseableQueueFactory(FooQueue,
    ...                                           "CloseableFooQueue")


The ``Closed`` exception class
------------------------------

Both the ``get`` and ``put`` methods of a CloseableQueue object
may raise ``Closed`` if called on a closed queue.

Note that ``get`` will only raise ``Closed`` if the queue is empty.


Iteration utility functions
---------------------------

Transformation of iterables to and from queues is made convenient via the
``enqueue`` and ``dequeue`` functions.

The ``EnqueueThread`` function provides a further layer of convenience.

Although designed to work with closeable queues,
these functions can also be meaningfully applied to other Queues.

See their docstrings for more information.


Tests
-----

The ``CloseableQueue`` test suite is based on, and reuses much of the code from,
the test suite for the standard library's Queue module.

Regression tests are performed on the CloseableQueue class,
in addition to tests of the closing functionality.

Although the tests are reasonably thorough,
the author is by no means an expert in the area of concurrency;
review by more experienced developers is quite welcome.

The test suite may provide guidance in the form of simplistic usage examples.

Some attempt has been made to write code which will work on older Pythons,
however testing has only been performed on Python 2.6,
and the author has little experience with older versions.


Distribution
------------

``CloseableQueue`` is available via PyPI, or from the `github repo`_.

.. _github repo: http://github.com/intuited/CloseableQueue


License
-------

The CloseableQueue module is licensed
under the permissive terms of the `FreeBSD license`_.

See the file COPYING for details.

.. _FreeBSD license: http://www.freebsd.org/copyright/freebsd-license.html
