"""fixture: an entry point that reaches a capability DYNAMICALLY."""

import importlib

if __name__ == "__main__":
    print(importlib.import_module("cap_dynamic").VALUE)
