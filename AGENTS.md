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

### Product opt-in

The bot does **not** enable 3.0B by default; the 2.0 `GroupBrain` behaviour path
is the product. To run 3.0B alongside it, set one environment variable — read
the same way `DISCORD_TOKEN` is, so it can come from the `.env` file
`load_dotenv()` already reads:

```
ENABLE_BIOLOGICAL_3_0=1
```

Accepted truthy values: `1`, `true`, `yes`, `on`. Absent or anything else means
off, which is the default. This coarse switch selects
`BiologicalMode.BIOLOGICAL_3_0` and enables the escape circuit; it enables
nothing else, and `BIOLOGICAL_CIRCUITS` defaults are unchanged for every other
importer.

With it on, `/status` appends the three existing escape-circuit signals under
their existing names:

```
3.0B escape-circuit signals (model output, 0-1): escape=0.00 flight=0.00 threat=1.00
  LIF model outputs, not probabilities or measurements
```

These are normalised 3.0B LIF escape-circuit outputs — not an escape
probability, not a decision, not a measurement, and not the 3.0D GFS model.
The 3.0D GFS model has no Discord entry point; see `3.0_RELEASE_SPEC.md`
sections 6 and 7.
