"""
robotic_master_controller.py — placeholder.

This file previously imported simself-side modules (instruction_library,
experience_archive, robotic_field_core) as if they were siblings in
fieldcore/src. They are not. Per Grok master plan: pick one primitive.
The canonical robot control lives in simself/src/robotic_field_core.py and

simself/src/harness/. Use the simself path, not this file.

Per Grok (segment 02, applied 2026-09-16): two SimSelf classes was a
defect. Same principle: two robot controllers is a defect. The canonical
robot control is simself/src/robotic_field_core.py.

Run:
    python simself/src/research/embodiment/godot_bridge.py
for the Godot bridge. The Godot side holds the avatar; the SimSelf side
holds the kernel.
"""
from __future__ import annotations

import sys


def main() -> int:
    print("robotic_master_controller.py is archived (per Grok master plan).")
    print("Use simself/src/robotic_field_core.py + simself/src/harness/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
