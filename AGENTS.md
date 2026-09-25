# AGENTS.md

## Test Commands

```bash
# Full test suite (exclude diagnostics - module not present)
python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py

# Biological brain tests only
python -m pytest tests/test_biological_brain.py -v --tb=short
```

## Lint / TypeCheck
No lint or typecheck commands are configured in this project.

## Biological Brain 3.0

The biological brain layer lives in `biological_brain/`. It is enabled via feature flags in `biological_brain/configuration.py`:

```python
BIOLOGICAL_CIRCUITS = {
    "escape": False,   # 3.0B escape circuit (12 neurons, 18 synapses)
    "feeding": False,
    "phototaxis": False,
}
```

Set to `True` and use `BiologicalMode.BIOLOGICAL_3_0` to activate.

The escape circuit implements the Drosophila short-mode escape pathway:
- Visual interneurons (LC4, LPLC2) -> Giant Fiber (GF) -> TTMn (jump) / PSI -> DLMn (wing downstroke)
- Loaded from `biological_brain/data/escape_circuit.json`
- Circuit name in `BiologicalBrain.circuits` is `"escape_core"`
