# Day 17 — Multi-Agent Concepts
**Date:** May 7, 2026

## What is Multi-Agent?
- Single agent = one Claude doing everything
- Multi-agent = multiple Claudes with specialized roles
- Orchestrator = manager, Subagent = worker

## Patterns
- Sequential: A → B → C
- Parallel: multiple agents same time → aggregator
- Hierarchical: orchestrator delegates to specialists

## Key Insight
- Agents can act in parallel with their own isolated context, which helps improve output quality and can also improve time to completion.

## Why It Matters
- Breaks token limit constraints
- Specialization = better output quality
- Scales to complex real-world tasks

## Tomorrow — Day 18
Build a multi-agent pipeline v1