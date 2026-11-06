"""fixture: a package. Its init reaches a module inside it."""

from . import mod_rel

if __name__ == "__main__":
    print(mod_rel.answer())
