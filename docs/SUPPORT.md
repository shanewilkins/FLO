# FLO Support Matrix

FLO `0.2.x` supports local, trusted-source authoring with Python 3.14 and Node.js 26. The Python package is platform-neutral; direct SVG layout invokes the bundled ELK JavaScript through the local Node runtime.

| Environment | Status | Evidence |
| --- | --- | --- |
| Ubuntu latest, Python 3.14, Node 26 | Supported target; hosted gate configured | full gate, clean-wheel import/help smoke, deterministic artifacts, and headless Chrome SVG consumption; the current change still requires its first hosted pass |
| macOS latest, Python 3.14, Node 26 | Supported target; hosted gate configured | clean-wheel import/help and scaffold→validate→render smoke; the current change still requires its first hosted pass |
| Windows | Not currently supported | no CI or maintainer validation; contributions require equivalent clean-wheel and render evidence |

Supported artifacts are the combinations listed by the renderer capability matrix. Chrome consumption proves that the maintained white-belt SVG opens and rasterizes in one browser engine; it is not a claim of complete browser, print, or assistive-technology coverage.

The source trust and resource boundary is defined in `policy/source_trust.md`. Hosted uploads and arbitrary untrusted source are outside the current support claim.
