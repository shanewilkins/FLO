"""Measure real browser glyph bounds and safe publication scaling for release SVGs."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEASURE = r"""
(async () => {
  await document.fonts.ready;
  const cases = [];
  for (const container of document.querySelectorAll('[data-case]')) {
    const svg = container.querySelector('svg');
    const view = svg.viewBox.baseVal;
    const issues = [];
    let minSize = Infinity, count = 0;
    const inside = (a,b) => a.x >= b.x-2 && a.y >= b.y-2 && a.x+a.width <= b.x+b.width+2 && a.y+a.height <= b.y+b.height+2;
    for (const text of svg.querySelectorAll('text')) {
      if (!text.textContent.trim()) continue;
      const box = text.getBBox();
      const matrix = text.getScreenCTM();
      const scale = Math.min(Math.hypot(matrix.a,matrix.b),Math.hypot(matrix.c,matrix.d));
      const size = parseFloat(getComputedStyle(text).fontSize);
      minSize = Math.min(minSize,size*scale); count++;
      const issue = reason => issues.push({reason,text:text.textContent,x:box.x,y:box.y,width:box.width,height:box.height});
      if (![box.x,box.y,box.width,box.height,scale].every(Number.isFinite) || box.width === 0) issue('invalid glyph bounds');
      if (scale < 0.75-0.001) issue('below safe fit scale');
      if (!inside(box,view)) issue('text outside SVG viewBox');
      const node = text.closest('[data-node-id]');
      if (node) {
        const shape = node.querySelector(':scope > rect, :scope > polygon, :scope > ellipse');
        if (shape && !inside(box,shape.getBBox())) issue('text outside node bounds');
      }
      if (text.closest('[data-edge-source]')) {
        let previous = text.previousElementSibling;
        while(previous && previous.tagName.toLowerCase() === 'text') previous=previous.previousElementSibling;
        if (previous && previous.tagName.toLowerCase() === 'rect' && !inside(box,previous.getBBox())) issue('text outside annotation bounds');
      }
    }
    cases.push({id:container.dataset.case,text_count:count,min_effective_font_px:minSize,issues});
  }
  const result={schema_version:1,browser:navigator.userAgent,scale_floor:0.75,cases};
  document.getElementById('result').textContent=JSON.stringify(result);
})();
"""


def parse_result(output: str) -> dict:
    """Extract a completed structured measurement, rejecting partial browser output."""
    match = re.search(r'<pre id="result">(.*?)</pre>', output, re.S)
    if match is None:
        raise ValueError("Browser did not return measurement results")
    result = json.loads(html.unescape(match.group(1)))
    if not result.get("cases") or any(
        case["text_count"] == 0 for case in result["cases"]
    ):
        raise ValueError("Browser did not measure every SVG")
    return result


def browser_failure(
    error: subprocess.TimeoutExpired | subprocess.CalledProcessError,
) -> dict:
    """Retain startup diagnostics while keeping unmeasured consumers failed."""
    stderr = error.stderr or ""
    if isinstance(stderr, bytes):
        stderr = stderr.decode(errors="replace")
    return {
        "schema_version": 1,
        "status": "browser_error",
        "cases": [],
        "error": type(error).__name__,
        "stderr_tail": stderr[-6000:],
    }


def main() -> int:
    """Run an isolated headless browser as an SVG consumer, never a render runtime."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--svg", type=Path, action="append")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="For isolated CI browser consumers only",
    )
    args = parser.parse_args()
    paths = args.svg or sorted((ROOT / "tests/golden/sppm").glob("*/render.svg"))
    with tempfile.TemporaryDirectory(prefix="flo-svg-consumer-") as temporary:
        workspace = Path(temporary)
        document = workspace / "measure.html"
        pieces = [
            "<!doctype html><meta charset=utf-8><style>body{margin:0}section{display:block}</style>"
        ]
        for path in paths:
            pieces.append(
                f'<section data-case="{html.escape(path.parent.name, quote=True)}">{path.read_text()}</section>'
            )
        pieces.append('<pre id="result"></pre><script>' + MEASURE + "</script>")
        document.write_text("\n".join(pieces))
        try:
            completed = subprocess.run(
                [
                    str(args.browser),
                    "--headless=new",
                    *(["--no-sandbox"] if args.no_sandbox else []),
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-background-networking",
                    "--enable-automation",
                    "--password-store=basic",
                    # Chromium's documented macOS flags avoid OS permission dialogs
                    # in a fresh test profile; no real user keychain is accessed.
                    # https://chromium.googlesource.com/chromium/src/+/HEAD/docs/mac_build_instructions.md
                    *(
                        [
                            "--use-mock-keychain",
                            "--disable-features=DialMediaRouteProvider",
                        ]
                        if sys.platform == "darwin"
                        else []
                    ),
                    f"--user-data-dir={workspace / 'profile'}",
                    "--virtual-time-budget=5000",
                    "--dump-dom",
                    document.as_uri(),
                ],
                capture_output=True,
                text=True,
                timeout=45,
                check=True,
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
            failure = browser_failure(error)
            output = json.dumps(failure, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(output)
            print(output, end="")
            return 1
        result = parse_result(completed.stdout)
    result["inputs"] = {
        str(path.relative_to(ROOT))
        if path.is_relative_to(ROOT)
        else str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    else:
        print(output, end="")
    return int(any(case["issues"] for case in result["cases"]))


if __name__ == "__main__":
    raise SystemExit(main())
