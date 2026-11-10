# Bundled third-party code

The renderer (`../render.py`) needs one package, so it ships here and a render never
installs anything. `render.py` puts this folder first on its import path.

| Package | Version | Licence | Source |
|---|---|---|---|
| beautifulsoup4 (`bs4/`) | 4.12.3 | MIT, see [LICENSES/beautifulsoup4-LICENSE.txt](LICENSES/beautifulsoup4-LICENSE.txt) | the PyPI wheel `beautifulsoup4-4.12.3-py3-none-any.whl` |

What differs from the wheel:

- `bs4/tests/` is left out (the package's own test suite).
- `bs4/dammit.py`: two comments that showed an en dash and an em dash glyph now name them
  ("en dash", "em dash"). The byte values on those lines are unchanged.
- `bs4/__init__.py`: the `__author__` string keeps the author's name and drops the email
  address, which this repository's leak scan refuses. Nothing reads that string.

What is not bundled: `soupsieve`, which beautifulsoup4 uses only for CSS selectors. The
renderer uses no CSS selectors, and `render.py` silences the one warning bs4 prints when
soupsieve is absent. If soupsieve is installed anyway, bs4 uses it as normal.

To update: replace `bs4/` with the same folder from a newer wheel, keep the two notes
above true, and run the tests.
