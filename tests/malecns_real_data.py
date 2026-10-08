"""Shared cached loaders for the MaleCNS real-data tests.

The syn-partners table is ~6.5 GB. Every real test needs the same
43 verified PSI->MN5 contacts, so the single extract is cached at
module scope and shared across every test file that imports this.
The contacts are frozen dataclasses and are never mutated.

This is test infrastructure only; it is not imported by any
production code.
"""
import os
import tempfile
from typing import Dict, List, Tuple

from biological_brain import malecns_ingest as mi

_SYN = os.path.join(
    tempfile.gettempdir(),
    "syn-partners-male-cns-v1.0-minconf-0.5.feather")

_CACHE: Dict[Tuple[int, int, int, int], List] = {}


def real_contacts() -> List:
    """The 43 verified PSI->MN5 contacts, streamed once per session."""
    key = (mi.PSI_LEFT, mi.PSI_RIGHT, mi.MN5_LEFT, mi.MN5_RIGHT)
    if key not in _CACHE:
        syn = mi.MaleCNSSynapses(_SYN)
        _CACHE[key] = syn.extract(
            [mi.PSI_LEFT, mi.PSI_RIGHT], [mi.MN5_LEFT, mi.MN5_RIGHT])
    return _CACHE[key]
