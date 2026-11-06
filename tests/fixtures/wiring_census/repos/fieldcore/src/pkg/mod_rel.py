"""fixture: relative imports -- one inside the package, one above it."""

from .result import helper
from .. import cap_top_level


def answer():
    return helper() + cap_top_level.VALUE
