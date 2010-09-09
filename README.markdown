`CloseableQueue`
================


The `CloseableQueue` class
--------------------------

The `CloseableQueue` class provides a means to permanently close a queue.

This is intended to provide queue support for functionality
  that would otherwise be implemented through the use of sentinel values
  or other mechanisms.
Such workarounds can be particularly awkward
  in the case of multi-consumer queues.

The CloseableQueue class provides both a `close` method
  and an extra parameter, `last`, to its `put` method.

Further details are available in the docstrings of the class and its methods.


Tests
-----

The CloseableQueue test suite is based on, and reuses much of the code from,
  the test suite for the standard library's Queue module.

Regression tests are performed on the CloseableQueue class,
  in addition to tests of the closing functionality.

Although reasonably thorough, the author is by no means an expert in the area
  of concurrency; review by more experienced coders is quite welcome.

The test suite may provide guidance in the form of simplistic usage examples.


License
-------

The CloseableQueue module is licensed under the terms of the [FreeBSD license].

See the file COPYING for details.

[FreeBSD license]: http://www.freebsd.org/copyright/freebsd-license.html
