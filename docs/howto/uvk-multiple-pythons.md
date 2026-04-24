<style>
    span.uvk {
        font-family: sans-serif;
    }
</style>


# <span class="uvk">uvk</span> kernels for multiple Python interpreters

For a given <span class="uvk">uvk</span> kernel,
the Python interpreter to use is fixed.
It can be set at [kernel install](../install.md) time by using the
[`--python`](../reference/uvk_cli.md#python-version) option.
Given that,
it may be frustrating when a notebook sets a constraint on the
[Python version](../reference/uvk_ext.md#uvk.require_python) that the interpreter
determined during installer does not meet.

Fortunately, in environments with Internet access, **uv** can gather distinct
Python interpreters on the fly.
For instance, one can run a script using Python 3.11 with a command such as

```sh
uv run --python 3.11 my-script.py
```

It is thus possible to install multiple parallel <span class="uvk">uvk</span> kernels
respectively running different minor versions of the Python interpreter.
The following UNIX pipeline sets up four [user-space](../reference/uvk_cli.md#user)
kernels, respectively for Python 3.11 to 3.14.

```sh
echo 3.11 3.12 3.13 3.14 \
    | xargs -n1 -I{} -- uvk --user --name uvk-{} --display-name 'uvk on v. {}' --python {}
```

One then has four <span class="uvk">uvk</span> kernels they may use whenever their
[default kernel](notebook-easiest-to-share.md#uvk-kernel-installation-convention)
does not satisfy some notebook's requirements.

Alternatively,
if one has their own Python installations through,
say,
a number of Conda environments,
these can be kernelized too.
We bank then on **uv**'s `--python` option also accepting the path to
the Python interpreter it should use.

```sh
echo my-env1 other-env some-project \
    | xargs -n1 -I{} -- uvk --user --name uvk-{} --display-name 'uvk over {}' --python "\$(conda run -n {} python -c 'import sys; print(sys.executable)')"
```
