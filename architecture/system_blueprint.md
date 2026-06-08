# 🏛️ SYSTEM MASTER BLUEPRINT - PROVARA/KESTREL
_Status: UPDATED_
_Architect: Kairos (Proactive Mode)_

## 🎯 Core Objective
Transition from a fragmented collection of scripts to a unified, autonomous execution engine.

## 🛠️ The Unified Pipeline
- **Ingestion:** Live Ingest $ightarrow$ Signal Normalizer $ightarrow$ Scoring Engine
- **Orchestration:** HUB_INTAKE $ightarrow$ Hop Protocol $ightarrow$ Agent Execution
- **Memory:** Daily Notes $ightarrow$ Memory Bank $ightarrow$ Provara Vault

## ⚡ Model Routing (The Primary Shift)
- **Primary:** `deepseek/deepseek-v4-flash` (Reasoning & Tool Execution)
- **Secondary:** `google/gemma-4-31b-it:free` (Low-cost fallback)

## 🚧 Immediate Technical Debt (The 'Hit List')
- [ ] **Path Unification:** All scripts must point to `/home/synczus/kestrel/core/unified/`.
- [ ] **Lock Resolution:** Fix the DuckDB lock conflicts (Zombie process cleanup).
- [ ] **Service Recovery:** Restore the Synapse server and Core main.py.
- [ ] **Signal Flow:** Verify signal flow from Ingest to Scoring Engine.

## 🗺️ System Map
- `/home/synczus/kestrel/core/unified/` - The Brain (Main logic, Scoring, Ingest)
- `/home/synczus/kestrel/identity/` - The Souls (Agent DNA)
- `/home/synczus/kestrel/scoring/` - The Filter (DuckDB, Scoring rules)
- `/home/synczus/projects/active/huntsystems/` - The Compound (Production artifacts)
