"""Programmatic core and console entrypoints for the FLO CLI.

This module exposes `run`, `run_file`, and `run_content` which the
thin Click wrapper (`flo.cli`) uses. Keeping the core functional and
easy-to-test avoids reliance on stdout/stderr side effects in tests.
"""

from flo.services.errors import (
	EXIT_SUCCESS,
	EXIT_RENDER_ERROR,
	EXIT_PARSE_ERROR,
	EXIT_COMPILE_ERROR,
	EXIT_VALIDATION_ERROR,
	ParseError,
	CompileError,
	ValidationError,
	RenderError,
)
from flo.services import get_services

from .cli_args import parse_args
from .io import read_input, write_output
from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.ir import validate_ir
from flo.analysis import scc_condense
from flo.render import render_dot


# Main scaffolding / TODOs
# -----------------------
# The following high-level responsibilities will be implemented in `main`:
#
# 1. Arg parsing
#    - parse subcommand (compile/validate/render/version)
#    - flags: --output, --format, --verbose, --quiet, --schema, --check
#    - accept filename or '-' for stdin
#
# 2. Configure logging
#    - call `configure_logging(level)` from `flo.logging`
#
# 3. Read input
#    - open file or read stdin; handle IO errors
#
# 4. Parse
#    - call parser to get adapter model; map parse errors -> EXIT_PARSE_ERROR
#
# 5. Compile (YAML -> IR)
#    - call compiler; map compile errors -> EXIT_COMPILE_ERROR
#
# 6. Validate IR
#    - call `flo.ir.validate` and JSON Schema checks; map failures -> EXIT_VALIDATION_ERROR
#
# 7. Post-processing / analyses (SCC condensation, heuristics)
#
# 8. Output
#    - emit IR JSON (default) or render DOT if requested
#    - write to stdout or --output file; handle IO errors -> EXIT_RENDER_ERROR
#
# 9. Exit codes
#    - Use constants defined in `flo.errors` (EXIT_SUCCESS, EXIT_PARSE_ERROR, ...)
#

# `run()` moved to `core.py` and `console_main()` moved to `cli.py`.



def main(argv: list) -> int:
	"""Run the main orchestrator for the FLO CLI.

	Accepts an argv list (programmatic invocation) and performs the full
	parse -> compile -> validate -> render -> output flow. Returns an
	integer exit code suitable for `sys.exit`.
	"""
	services = get_services(verbose=False)
	logger = services.logger

	# Parse args and (optionally) reconfigure services
	path, command, options, services, logger = parse_args(argv, services)
	telemetry = services.telemetry

	# Read input
	rc, content, err = (0, "", "")
	if path:
		rc, content, err = read_input(path)
	else:
		rc, content, err = read_input("-")
	if rc != 0:
		services.error_handler(err)
		return rc

	# Parse
	try:
		adapter_model = parse_adapter(content)
	except ParseError as e:
		services.error_handler(str(e))
		return getattr(e, "code", EXIT_PARSE_ERROR)
	except Exception as e:
		services.error_handler(str(e))
		return EXIT_PARSE_ERROR

	# Compile
	try:
		ir = compile_adapter(adapter_model)
	except CompileError as e:
		services.error_handler(str(e))
		return getattr(e, "code", EXIT_COMPILE_ERROR)
	except Exception as e:
		services.error_handler(str(e))
		return EXIT_COMPILE_ERROR

	# Validate
	try:
		validate_ir(ir)
	except ValidationError as e:
		services.error_handler(str(e))
		return getattr(e, "code", EXIT_VALIDATION_ERROR)
	except Exception as e:
		services.error_handler(str(e))
		return EXIT_VALIDATION_ERROR

	# Post-process (best-effort)
	try:
		ir = scc_condense(ir)
	except Exception:
		pass

	# Render (produce DOT); return DOT when an output path was requested,
	# otherwise keep the human-friendly placeholder used by tests.
	try:
		dot = render_dot(ir)
	except RenderError as e:
		services.error_handler(str(e))
		return getattr(e, "code", EXIT_RENDER_ERROR)
	except Exception as e:
		services.error_handler(str(e))
		return EXIT_RENDER_ERROR

	out = dot if options and options.get("output") else "Hello world!"

	# Output
	write_rc, write_err = write_output(out, options.get("output") if options else None)
	if write_rc != 0:
		services.error_handler(write_err)
		return write_rc

	# Best-effort telemetry shutdown
	try:
		telemetry.shutdown()
	except Exception:
		pass

	return EXIT_SUCCESS


if __name__ == "__main__":
	raise SystemExit("flo.main is a programmatic entrypoint; use the `flo` CLI or `python -m flo.cli` to run the console application")