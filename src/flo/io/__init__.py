"""Compatibility shim for `flo.io` that forwards to `flo.services.io`.

Package form so `from flo.io import read_input` continues to work.
"""
from flo.services.io import read_input, write_output

__all__ = ["read_input", "write_output"]
