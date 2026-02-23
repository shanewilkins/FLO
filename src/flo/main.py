from typing import Tuple

from flo.services.errors import (
	CLIError,
	EXIT_SUCCESS,
	EXIT_USAGE,
	EXIT_PARSE_ERROR,
	EXIT_COMPILE_ERROR,
	EXIT_VALIDATION_ERROR,
	EXIT_RENDER_ERROR,
)
from flo.services import get_services


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

def run() -> Tuple[int, str, str]:
	"""Core function returning (exit_code, stdout, stderr).

	Returning structured output makes the functional contract explicit and
	easy to test without relying on stdout/stderr side effects.
	For now this is a placeholder; it will later be refactored into
	`run_content(content, command, options)` and `run_file(path, ...)`.
	"""
	return EXIT_SUCCESS, "Hello world!", ""


def run_content(content: str, command: str = "compile", options: dict | None = None) -> Tuple[int, str, str]:
	"""Functional core: operate on file content.

	- `command` may be `compile` or `validate` for v0.1.
	- `options` is a placeholder dict for future flags (schema path, etc.).

	This is a thin placeholder: later this will call parser/compile/validate
	and return (rc, stdout, stderr).
	"""
	# TODO: call parser, compiler, and validator here.
	return EXIT_SUCCESS, "Hello world!", ""


def run_file(path: str, command: str = "compile", options: dict | None = None) -> Tuple[int, str, str]:
	"""Read `path` and delegate to `run_content`.

	Returns the same (rc, stdout, stderr) tuple.
	"""
	try:
		if path == "-":
			import sys

			content = sys.stdin.read()
		else:
			with open(path, "r", encoding="utf-8") as fh:
				content = fh.read()
	except OSError as e:
		return EXIT_RENDER_ERROR, "", f"I/O error reading {path}: {e}"
	return run_content(content, command=command, options=options)


def main(argv: list | None = None) -> int:
	"""Console entrypoint for the `flo` script.

	Implementation plan (stepwise):
	- Parse CLI args (keep CLI parsing thin; accept `argv=None` in future)
	- Configure logging with `configure_logging()`
	- Read input (file or stdin)
	- Call functional core to `run_content()` (parse/compile/validate)
	- On errors, use `handle_error()` and return mapped exit codes
	- Print stdout/stderr and return rc
	"""
	# Create services early with default (non-verbose) logging. If the
	# user requests verbosity we re-create services below with debug
	# level; `get_services` is idempotent about configuring logging.
	services = get_services(verbose=False)
	logger = services.logger

	# Minimal arg parsing: if `argv` is provided, parse it; otherwise use
	# default behavior (no args) for backwards compatibility in tests.
	command = "compile"
	options: dict = {}
	path: str | None = None

	if argv is not None:
		import argparse

		parser = argparse.ArgumentParser(prog="flo")
		parser.add_argument("path", nargs="?", help="Path to .flo file (or - for stdin)")
		parser.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity")
		parser.add_argument("-o", "--output", help="Write output to file instead of stdout")
		parser.add_argument("--validate", action="store_true", help="Only validate the file")
		parsed = parser.parse_args(argv)
		path = parsed.path
		options["verbose"] = bool(parsed.verbose)
		options["output"] = parsed.output
		if parsed.validate:
			command = "validate"

		# Reconfigure services if verbose was requested so logging level
		# can be elevated for the remainder of execution.
		if options.get("verbose"):
			services = get_services(verbose=True)
			logger = services.logger

	# Run core logic inside an optional telemetry span and ensure we
	# always shutdown telemetry before exiting the process.
	telemetry = services.telemetry

	# Defaults
	rc = EXIT_SUCCESS
	out = ""
	err = ""

	try:
		if getattr(telemetry, "tracer", None) is not None:
			# type: ignore[attr-defined]
			with telemetry.tracer.start_as_current_span("cli.run") as span:  # type: ignore[attr-defined]
				if path:
					rc, out, err = run_file(path, command=command, options=options)
				else:
					rc, out, err = run()
				# attach some simple attributes to the span
				try:
					span.set_attribute("cli.command", command)
					if path:
						span.set_attribute("cli.path", path)
				except Exception:
					pass
		else:
			if path:
				rc, out, err = run_file(path, command=command, options=options)
			else:
				rc, out, err = run()
	except CLIError as e:
		services.error_handler(str(e))
		rc = getattr(e, "code", EXIT_USAGE)
	except Exception as e:  # pragma: no cover - top-level unexpected
		services.error_handler(f"Unexpected error: {e}")
		rc = EXIT_USAGE

	import sys

	if out:
		print(out)
		logger.info("stdout", message=out)
	if err:
		print(err, file=sys.stderr)
		# Delegate error handling/logging to the services error handler.
		services.error_handler(err)

	# Best-effort telemetry shutdown to flush exporters.
	try:
		telemetry.shutdown()
	except Exception:
		pass

	return rc


if __name__ == "__main__":
	raise SystemExit(main())