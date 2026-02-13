# uvk -- Fully isolated IPython kernels based on uv

Proper documentation TBD... In the meantime:

1. Install `uvk` in an environment from which you run Jupyter Lab / Notebook.
1. Invoke `uvk` from this environment to install the UVK kernel attached to the Python executable of your environment.
    - Distinct icon TBD
1. Use kernel `UVK (Python 3.xx)` in your notebooks

and 🎉 your Python kernel runs out of a temporary, isolated environment.
Check it out by running a notebook with a code cell going

```python
import sys
sys.prefix
```

and see how every time you restart the kernel, the prefix directory changes.

Feature wishlist:

- Python version validation against a constraint with a magic
- Magic for adding dependencies on the fly
- Magic for including [inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata)
- Integration with uv project workflows
- Python version and executable management through duly-named alternate kernels
