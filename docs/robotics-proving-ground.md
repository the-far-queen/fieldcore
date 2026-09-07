# FieldCore Robotics — top-level concept (2026-09-05)

**Source:** Bobby's notes. Status: this is a **product/platform pitch**, not engineering for SimSelf or kernel code.

## What this is

A "modern robotics proving ground" where learning, building, validation are the same continuous process. Claims (controller stability, navigation policy, manipulation success) progress through a ladder:

1. Text/paper-level claims
2. Simulation-backed claims
3. Reproducible simulation results
4. Hardware-validated claims
5. Scarce real-robot access (earned)

**FieldCore as governing logic** — accepts or rejects admissible states. Not a code host, not a school, not a chat community. Replaces resumes/portfolios/demo days with provable work.

## Why robotics first

Robotics has objective metrics, demands control theory, resists hype, exposes shallow thinking quickly.

## Status

This is **NOT load-bearing for the current SimSelf / FieldCore kernel work.** The kernel is the math substrate; this is a future platform that would run on top of it. No code here. No implementation. No clients.

## Why not in either repo

- fieldcore repo = math substrate + Python implementation + design docs
- simself repo = identity layer + kernel code
- Neither is a platform/pitch document

This document needs its own home if Bobby decides to pursue it:
- New repo: `fieldcore-robotics` or `the-proving-ground`?
- Or stay as a private vision doc in vault?

## Open

- Is this a real venture idea, or aspirational writing?
- Does it need funding / partners / team, or is it exploratory?
- Where does it sit relative to the 17network work mentioned in earlier handoffs?

---
*Captured 2026-09-05. Saved as deferred/separate. Does not belong in fieldcore or simself repo.*