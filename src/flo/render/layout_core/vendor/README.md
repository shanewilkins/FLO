# Vendored ELK runtime

FLO distributions include `elkjs` 0.12.0's `lib/elk.bundled.js` so rendering
does not depend on an adjacent `node_modules` directory. The generated bundle
and its `ELKJS_LICENSE.md` are copied from the pinned npm dependency by
`scripts/vendor_elkjs.py` before distribution builds.

Source: <https://github.com/kieler/elkjs/tree/0.12.0>

License: EPL-2.0 OR GPL-3.0-or-later, as declared by `elkjs` 0.12.0.

Do not edit the generated files by hand. Update `package.json` and
`package-lock.json`, run the vendoring script, and exercise the clean-wheel
render smoke test instead.
