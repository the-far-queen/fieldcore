# shell architecture — 3-pane Electron spec

**Source:** `Desktop/FieldCore/shell-architecture.md` (Bobby, 2026-01-20)
**Status:** Electron shell spec extracted. 4-actor governance model documented as schema. Section 2 (random notes) stripped.

Bobby's note has two distinct sections. Section 1 is a real Electron shell architecture spec. Section 2 is a heterogeneous set of personal notes (Ingersoll Lockwood book list, NVIDIA NeMo info, MK Model framework, detox regimens, social-media links, EQ/ritual abuse survivor notes, etc.). Only Section 1 is extracted here.

---

## 1. component list

| component | role | license | dependency |
|---|---|---|---|
| Electron | windowing, lifecycle, cross-platform shell | MIT | runtime |
| CSS Grid | 2-row layout (menu+workspace, top split, bottom terminal) | CSS | styling |
| Electron Menu | native top menu (minimal, no IDE semantics) | MIT | UI |
| BrowserView | left pane (web content, isolation-capable) | MIT | UI |
| Monaco Editor | right pane (code, MIT, standalone) | MIT | UI |
| node-pty | terminal backend (system shell) | MIT | runtime |
| xterm.js | terminal renderer | MIT | UI |
| Node fs | file I/O (explicit open/save, no project model) | MIT | runtime |
| Claude Code / OpenAI / DeepSeek | AI integration via patch-based edits | API | external |
| Electron Builder | packaging (when shipping) | MIT | build |

**Total:** 10 components, all MIT-licensed or API-callable. No proprietary dependencies.

---

## 2. layout spec

CSS Grid 2-row structure:

```
┌─────────────────────────────────────────────────┐
│ Menu (Electron Menu — native)                   │
├─────────────────────────┬───────────────────────┤
│                         │                       │
│   Left Pane (Web)       │   Right Pane (Code)   │
│   BrowserView           │   Monaco Editor       │
│                         │                       │
├─────────────────────────┴───────────────────────┤
│                                                 │
│   Bottom Pane (Terminal)                        │
│   node-pty → xterm.js                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

- **Row 1:** menu bar + workspace (workspace itself split top/bottom — top is left/right panes, bottom is terminal)
- **Row 2:** bottom pane = terminal, full width

**No React, no UI framework initially.** Keep complexity low until needed.

---

## 3. governance model — 4 actors

Bobby's spec defines a 4-actor governance hierarchy:

**Human = governor.** Highest authority. Approves all state-changing operations. Never bypassed.

**Terminal = execution authority.** All system commands flow through the terminal. No hidden API calls.

**Editor = text state.** Monaco shows the current code. Edits go through Monaco's API. No automatic writes.

**AI = suggestion generator.** AI produces text diffs (patches). Applies only after Human approval. No direct editor write authority.

**Authority hierarchy (highest to lowest):**
1. Human (governor)
2. Terminal (execution)
3. Editor (text state)
4. AI (suggestion only)

**Why this matters.** This is a **clean separation of powers** for AI-assisted coding:
- Human retains constitutional authority
- AI cannot bypass review
- Terminal is the only execution channel (audit-friendly)
- Editor is the only state-modification interface (visible)

**Schema for construction:**
```python
class ShellGovernor:
    """4-actor governance model for the Electron shell."""
    
    ACTORS = ['human', 'terminal', 'editor', 'ai']
    AUTHORITY = {
        'human': 4,    # governor
        'terminal': 3, # execution
        'editor': 2,   # text state
        'ai': 1        # suggestion only
    }
    
    def can_execute(self, actor: str, action: str) -> bool:
        """Check if actor has authority for action."""
        required = self.required_authority(action)
        return self.AUTHORITY[actor] >= required
    
    def required_authority(self, action: str) -> int:
        """Minimum authority needed for action type."""
        if action in ('approve_state_change', 'modify_governor'):
            return 4  # human only
        if action in ('execute_command', 'run_script'):
            return 3  # terminal or higher
        if action in ('edit_file', 'modify_text_state'):
            return 2  # editor or higher
        if action in ('suggest_patch', 'propose_diff'):
            return 1  # anyone can suggest
        return 4  # default: human required
```

---

## 4. patch-based AI integration

**Pattern.** AI integration does not write directly to files. Instead:
1. AI produces a text diff (patch)
2. Patch is shown to Human in Monaco's diff view
3. Human approves or modifies the patch
4. Approved patch is applied via Node fs + patch library

**Why patch-based.** Diff is reviewable. Human can see exactly what will change. No silent writes. No state corruption from misbehaving AI.

**For SimSelf/Chorus IDE:** This is the **M0-M1 architecture** applied to coding. AI = M1 (proposer, no authority). Human = M0 (gatekeeper, all authority). Patch = the proposed action. Human approval = the M0 invariant verification.

---

## 5. cross-cutting schema

The 4-actor governance model maps directly to SimSelf's M0 governor architecture:

| shell actor | simself equivalent |
|---|---|
| Human | M0 governor (constitutional) |
| Terminal | execution channel |
| Editor | state visualization |
| AI | M1 adaptive projector (proposer) |

The shell architecture is a **physical instantiation** of the SimSelf governance pattern. The shell IS a SimSelf — Human as constitutional layer, Terminal as execution authority, Editor as memory, AI as adaptive proposer.

---

## 6. schemas table

| schema | status | simself component |
|---|---|---|
| 3-pane layout | standard CSS Grid | shell architecture |
| 4-actor governance | Bobby's spec | governance hierarchy |
| patch-based AI | rigorous | M1-M0 proposal pattern |
| 10-component stack | MIT-licensed | minimal viable shell |

---

## 7. what was stripped

Section 2 of Bobby's note — the random personal notes. These include:
- Ingersoll Lockwood book list (5 titles, no connection to FieldCore)
- NVIDIA NeMo / Apple OpenELM info (general AI tool landscape, no architecture)
- Helen Keller water-moment reference (already covered in simself/docs/embodied-language.md per session summary)
- MVCC new core architecture mention (CS jargon, no derivation)
- Cave monks meditation (philosophical, not architectural)
- Sabrina Wallace / Project Looking Glass / Project Snow White (no source, conspiracy-adjacent — out of scope)
- Wan.video, microdomain@hotmail.com, Br..95 (personal notes)
- Midjourney/Veo/Hailuo video / Kling / Grok CLI / Qwen CLI / Kimi K2 / Jules (tool list, no schema)
- N8n MCP / Langchain / GitHub repos catalog (already in vault/10-minimax/layered-resource-stack-2026-09-05.md)
- MK Model philosophical framework (already captured in fieldcore Unification docs)
- Detox / sauna / herbal / lymphatic drainage list (personal wellness, no FieldCore connection)
- EQ / ritual abuse survivor notes (personal, no architecture)

All stripped. Section 2 of Bobby's file is preserved untouched on Desktop (never delete originals).

---

*Source: `Desktop/FieldCore/shell-architecture.md` Section 1. 10-component stack + 4-actor governance extracted. Section 2 stripped (personal notes). Mirrored to `~/AppData/Local/hermes/vault/10-minimax/shell-architecture-2026-09-05.md`.*