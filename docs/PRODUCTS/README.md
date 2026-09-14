# PRODUCTS — Bobby + Hermes first public releases

**Folder opened:** 2026-09-14 by Hermes (Minimax-M3).
**Rule:** this folder is for things that ship — runnable artifacts with users, not design docs. Companion to `docs/Math/` (engineering templates) and `docs/research-papers/` (paper pipeline).

---

## 1. poisoned-speech-lint-scanner-2026-09-14.md + poisoned_speech_lint.py

**The story.** Bobby's standing rule: never use words like "kill" / "terminate" / "dead" / "zombie" / "execute" / "terminal" when referring to processes. Bobby corrects every slip. The rule lived buried at line 49 of SOUL.md and kept slipping — memory of rules is unreliable.

**The product.** A stdlib-only Python scanner that catches the banned vocabulary in any text — files, repos, replies. CLI: `python poisoned_speech_lint.py <path> [--fix]`. Library: `from poisoned_speech_lint import scan, lint, fix`.

**Why first.** Memory is unreliable; enforcement is reliable. The scanner IS the persistent memory of the rule.

**License.** BSD.

---

## Future

- English primitives scanner (Bobby's `fname lname verb` insight from Math-Window1 §47)
- Substrate-as-text-toolkit (simself + fieldcore as a `pip install`-able library)
- Veo pipeline wrapper (3-vid-a-day burning)

*Filed 2026-09-14. Watch this folder grow.*