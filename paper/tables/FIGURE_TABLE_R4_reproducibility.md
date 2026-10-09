**Table R-4.** Reproducibility and validation status. The test count is inherited, not freshly executed [C-602, C-701].

| Item | Value | Status | Evidence class |
|---|---|---|---|
| Repository test suite | 1773 passed / 2 skipped (excluding diagnostics) | INHERITED | AM (software) |
| Test command | `python -m pytest tests/ -v --tb=short --ignore=tests/test_diagnostics.py` | VERIFIED | AM |
| SWC SHA-256 pinning (sensitivity script) | 2 cached MN5 SWCs pinned | SHA-256 confirmed in script | AM |
| MaleCNS synapse Feather checksum | NOT RECORDED | VERIFY_REQUIRED | — |
| Data download/staging commands | NOT DOCUMENTED in repo | VERIFY_REQUIRED | — |
| External data license/attribution | VERIFY_REQUIRED | VERIFY_REQUIRED | — |
| Model sensitivity rows | 15,528 (9,288 local + 2,880 abstract + 2,880 Dα7 + 480 cal) | GENERATED | MDE |

> Software validation is not empirical biological validation [C-602].