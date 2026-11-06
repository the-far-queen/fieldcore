"""fixture: a DECOY with the same leaf name as pkg/result.py.

Nothing imports it. If the census resolves a relative import to the
wrong place, this one reads as wired -- and that is the false positive
the fixture exists to catch.
"""

VALUE = 7
