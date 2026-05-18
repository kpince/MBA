# MBA Agent

MBA Agent is an experimental toolkit for AI agents working over markdown vaults.

It builds lightweight Markov blanket-style activation fields from an Obsidian-style vault, then produces bounded reports an agent can use instead of dumping raw notes into context.

This is not a memory solution, not a theory validator, and not a claim that Markov blankets magically solve agent continuity.

It is an invitation to test a narrower idea:

> Can an agent use structured activation boundaries to preserve conceptual orientation while staying inspectable?

## Status

Experimental. Expect rough edges.

The useful question is not “does this prove the model works?”

The useful question is:

> When an agent uses this layer, does its reasoning become more stable, more bounded, and easier to audit?

## Install

From a cloned repo:

```bash
sh install.sh
```

For a future GitHub install:

```bash
curl -fsSL https://raw.githubusercontent.com/YOU/mba-agent/main/install.sh | \
  MBA_AGENT_TARBALL_URL=https://github.com/YOU/mba-agent/archive/refs/heads/main.tar.gz sh
```

The installer links `mba` into `~/.local/bin` and copies the bundled skill into `~/.codex/skills/mba-adversarial-evaluator`.

You can override install locations:

```bash
MBA_BIN_DIR=/usr/local/bin MBA_SKILL_HOME=~/.codex/skills sh install.sh
```

## Usage

```bash
mba doctor
mba blanket --vault ./vault --seed Thuion.md --query "memory coherence bias"
mba field --vault ./vault --seed Thuion.md --query "what follows next?"
mba adversarial --vault ./vault --seed Thuion.md
```

`mba adversarial` writes:

```text
./vault/.markov/adversarial-evaluation.json
```

## What To Test

Try it on a real markdown vault.

Look for:

- irrelevant notes entering the blanket
- important notes missing from the blanket
- adversarial probes collapsing into vague attractors
- app-layer bias shaping the result
- reports that feel useful to an agent versus merely plausible

If it fails, the failure is useful. Open an issue with the command, vault shape, and output report.

## What It Does Not Do

- It does not require Obsidian.
- It does not use embeddings.
- It does not call an LLM.
- It does not mutate notes.
- It does not prove or disprove a theory.

The Python implementation uses the standard library only.
