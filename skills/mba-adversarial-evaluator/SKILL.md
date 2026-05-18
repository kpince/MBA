---
name: mba-adversarial-evaluator
description: Use when an AI agent needs to inspect an Obsidian-style markdown vault through a Markov blanket activation layer, reconstruct a bounded cognitive field, or run adversarial probes such as circularity, falsifiability gap, scope creep, metaphor leakage, escape hatch, and app-layer bias. Use this instead of dumping raw vault notes into context.
---

# MBA Adversarial Evaluator

Use this skill to route markdown-vault reasoning through a bounded app layer:

```text
vault/index data -> active blanket -> cognitive field -> report -> answer
```

Do not paste raw vault notes into chat unless the user explicitly asks for raw note inspection. Prefer JSON reports and bounded cognitive fields.

## Commands

From the repo root, or after installing the `mba` CLI:

```bash
mba doctor
mba blanket --vault /path/to/vault --seed Thuion.md --query "memory coherence bias"
mba field --vault /path/to/vault --seed Thuion.md --query "what follows next?"
mba adversarial --vault /path/to/vault --seed Thuion.md
```

`mba adversarial` writes:

```text
/path/to/vault/.markov/adversarial-evaluation.json
```

## Interpretation Rules

- Treat reports as diagnostic, not authoritative.
- High adversarial scores do not prove a theory false; they show where the field absorbs critique too easily.
- If the user asks for a conceptual answer, answer from the bounded report/field and state that you used reconstructed MBA output.
- If the user asks for a developer/debugging answer, inspect paths, scores, reasons, and report structure.

## Scripts

The portable implementation lives in `scripts/`:

- `mba_index.py`: markdown vault index
- `mba_blanket.py`: active blanket computation
- `mba_field.py`: bounded cognitive field reconstruction
- `mba_adversarial.py`: fixed adversarial probe runner

The scripts use Python standard library only.
