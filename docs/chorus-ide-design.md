# Chorus — Multi-Agent IDE Design

**Status:** design intent. Not built. Sourced 2026-09-05 from Bobby's notes (originally `z26.txt`).

## Concept

VS Code extension fork of Roo Code. Multi-agent panel where 2-3 AI models review same code simultaneously, debate, reach synthesized verdict. All in editor.

## Modes

| Mode | Behavior |
|---|---|
| Quick | All agents fire at once, no shared context |
| Debate | Round 1 independent → Round 2 each agent gets others' R1 as context |
| Chain | Sequential — A → B refines → C verdict |

## File structure

```
src/
├── agents/
│   ├── AgentManager.ts          ← parallel calls, debate/chaining
│   ├── callers/
│   │   ├── [provider]Caller.ts  ← one per AI provider
│   │   └── ...
│   └── modes/
│       ├── QuickMode.ts
│       ├── DebateMode.ts
│       └── ChainMode.ts
├── panels/
│   └── ChorusPanel.ts
webview-ui/src/
├── components/
│   ├── AgentColumn.tsx
│   ├── DebateView.tsx
│   ├── ChainView.tsx
│   ├── ConsensusBar.tsx
│   └── ModeSelector.tsx
└── ChorusApp.tsx
```

## Core types

```typescript
interface AgentReply {
  agent: string
  round: number
  content: string
  durationMs: number
}

class AgentManager {
  async quickRound(prompt): Promise<AgentReply[]>      // parallel
  async debateRound(prompt, r1Results): Promise<AgentReply[]>  // with rebuttals
  async *chainGenerator(prompt): AsyncGenerator<AgentReply>  // sequential
}
```

## Caller pattern (same interface per provider)

Each provider implements `call(prompt) → Promise<string>`. Anthropic SDK for MiniMax, subprocess for Gemini CLI, fetch for OpenAI-compatible local server.

## Consensus

After debate completes, send all replies to one fast model. Extract: agreed points, splits, unresolved. JSON response → UI bar.

## Phased build

| Phase | Scope | Effort |
|---|---|---|
| 1 | AgentManager + callers + side-by-side | ~2-3 days |
| 2 | Debate round 2 with context passing | ~1 day |
| 3 | Chain with streaming step-by-step | ~1-2 days |
| 4 | Consensus bar + analysis | ~1-2 days |
| 5 | Right-click, file review, settings | ~1 day |
| 6 | Polish, error handling, VSIX packaging | ~1 day |

Total: 1-2 weeks solo, faster with AI assistance.

## Why Chorus

Single-model coding assistants can't argue with themselves. Chorus gives each agent the others' outputs as context. The disagreement surface is the signal — where they agree, ship; where they split, look closer.

## Stale from source

Original called out "minimax" and "openclaw" as agent names — both internal/wrong. Use provider names (MiniMax, Gemini, Claude, etc.) at call time. Caller file naming follows provider, not internal nickname.

## Open

- Which 3 agents ship in v1? Likely Grok + Claude + MiniMax based on current stack.
- Is the consensus pass worth the cost, or just show the raw debate?
- Does Chorus integrate with the Bobby+5-model dev team workflow from 2026-09-05, or stand alone?
- Repo location: separate GitHub repo, or inside fieldcore?

---
*Sourced 2026-09-05. Design preserved. Caller names corrected.*