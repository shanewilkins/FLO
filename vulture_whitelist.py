"""Vulture whitelist for current intentional/known false positives.

This module defines a `whitelist` list used when invoking Vulture so CI
reports focus on new/unexpected findings. Items added here are expected to
be temporary for v0.1 and should be removed (un-whitelisted) as the
corresponding features are implemented.
"""

whitelist = [
	"run_cmd",
	"DECISION",
	"START",
	"END",
	"POOL",
	"NUMBER",
	"TIMESTAMP",
	"fm_cli",
	"_.shutdown_called",
	"_.shutdown_called",
	"_.shutdown_called",
	"_.shutdown_called",
	"exc",
	"exc_type",
	"tb",
	"_._shutdown_called",
	"_._shutdown_called",
	"_._shutdown_called",
	"_.shutdown_called",
	"_.shutdown_called",
]
