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
	map_exception_to_rc,
)
from flo.services.telemetry import get_tracer
import time
from flo.services import get_services

from .core.cli_args import parse_args
from flo.services.io import read_input, write_output
from flo.adapters import parse_adapter
from flo.compiler import compile_adapter
from flo.compiler.ir import validate_ir
from flo.compiler.analysis import scc_condense
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



def _parse_args_and_services(argv: list):
	services = get_services(verbose=False)
	logger = services.logger
	path, command, options, services, logger = parse_args(argv, services)
	return path, command, options, services, logger


def _read_input_or_stdin(path: str | None, services):
	if path:
		return read_input(path)
	return read_input("-")


def _parse_adapter(content: str, services):
	try:
		return parse_adapter(content), 0
	except ParseError as e:
		services.error_handler(str(e))
		return None, getattr(e, "code", EXIT_PARSE_ERROR)
	except Exception as e:
		services.error_handler(str(e))
		return None, EXIT_PARSE_ERROR


def _compile_adapter(adapter_model, services):
	try:
		return compile_adapter(adapter_model), 0
	except CompileError as e:
		services.error_handler(str(e))
		return None, getattr(e, "code", EXIT_COMPILE_ERROR)
	except Exception as e:
		services.error_handler(str(e))
		return None, EXIT_COMPILE_ERROR


def _validate_ir_instance(ir, services):
	try:
		validate_ir(ir)
		return 0
	except ValidationError as e:
		services.error_handler(str(e))
		return getattr(e, "code", EXIT_VALIDATION_ERROR)
	except Exception as e:
		services.error_handler(str(e))
		return EXIT_VALIDATION_ERROR


def _postprocess_ir(ir):
	try:
		return scc_condense(ir)
	except Exception:
		return ir


def _render_ir_and_output(ir, options, services):
	try:
		dot = render_dot(ir)
	except RenderError as e:
		services.error_handler(str(e))
		return getattr(e, "code", EXIT_RENDER_ERROR)
	except Exception as e:
		services.error_handler(str(e))
		return EXIT_RENDER_ERROR

	out = dot
	write_rc, write_err = write_output(out, options.get("output") if options else None)
	if write_rc != 0:
		services.error_handler(write_err)
		return write_rc
	return EXIT_SUCCESS


def main(argv: list) -> int:
	"""Run the main orchestrator for the FLO CLI.

	Accepts an argv list (programmatic invocation) and performs the full
	parse -> compile -> validate -> render -> output flow. Returns an
	integer exit code suitable for `sys.exit`.
	"""
	path, command, options, services, logger = _parse_args_and_services(argv)
	telemetry = services.telemetry

	tracer = get_tracer("flo.pipeline")

	start: float | None = None

	def _run_pipeline() -> int:
		"""Run pipeline steps inside a tracer span and return final rc."""
		nonlocal start
		with tracer.start_as_current_span("pipeline.run") as span:
			start = time.perf_counter()
			# Read input
			rc, content, err = _read_input_or_stdin(path, services)
			if rc != 0:
				services.error_handler(err)
				return rc

			adapter_model, rc = _parse_adapter(content, services)
			if rc != 0:
				return rc

			ir, rc = _compile_adapter(adapter_model, services)
			if rc != 0:
				return rc

			rc = _validate_ir_instance(ir, services)
			if rc != 0:
				return rc

			ir = _postprocess_ir(ir)

			rc = _render_ir_and_output(ir, options, services)

			# attach final rc and duration to span if supported
			try:
				duration_ms = int((time.perf_counter() - start) * 1000)
				setter = getattr(span, "set_attribute", None)
				if callable(setter):
					setter("pipeline.rc", int(rc or EXIT_SUCCESS))
					setter("pipeline.duration_ms", duration_ms)
					setter("pipeline.status", "ok" if int(rc or EXIT_SUCCESS) == 0 else "error")
			except Exception:
				pass

			return int(rc or EXIT_SUCCESS)

	# Orchestrate pipeline with centralized exception mapping
	try:
		return _run_pipeline()
	except Exception as e:
		rc, msg, internal = map_exception_to_rc(e)
		if internal:
			# unexpected/internal: log exception with traceback
			try:
				services.logger.exception(msg)
			except Exception:
				pass
		# Surface user-facing message for domain errors or fallback
		try:
			services.error_handler(msg)
		except Exception:
			pass

		# best-effort: attach error info and duration to telemetry root span
		try:
				with tracer.start_as_current_span("pipeline.error") as err_span:
					# Ensure `start` is not None before subtracting (type-safe)
					duration_ms = int((time.perf_counter() - start) * 1000) if start is not None else None
				setter = getattr(err_span, "set_attribute", None)
				if callable(setter):
					setter("pipeline.error", True)
					setter("pipeline.internal", bool(internal))
					setter("pipeline.error_message", msg)
					if duration_ms is not None:
						setter("pipeline.duration_ms", duration_ms)
		except Exception:
			pass

		# Best-effort telemetry shutdown
		try:
			telemetry.shutdown()
		except Exception:
			pass

		return int(rc)


if __name__ == "__main__":
	raise SystemExit("flo.main is a programmatic entrypoint; use the `flo` CLI or `python -m flo.cli` to run the console application")