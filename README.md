# pytoolset

A collection of Python utility functions.

## Installation

**Option 1 — Install directly from GitHub:**

```bash
pip install git+https://github.com/wbvguo/pytoolset.git
```

<!-- 
Or pin to a specific release:

```bash
pip install git+https://github.com/wbvguo/pytoolset.git@v0.1.0
``` -->

**Option 2 — Clone and install in editable mode (for development):**

```bash
git clone https://github.com/wbvguo/pytoolset.git
cd pytoolset
pip install -e .
```

<!-- 
## Usage

### `find_project_root`

Walk upward from a given path until a project marker file is found.

```python
from pytoolset import find_project_root

# defaults to looking for pyproject.toml
root = find_project_root()

# custom marker (e.g. Quarto projects)
root = find_project_root(anchor="/path/to/file.qmd", marker="_quarto.yml")
```

Raises `FileNotFoundError` if the marker is not found in any parent directory.
 -->
