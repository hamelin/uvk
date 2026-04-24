<style>
  span.uvk {
    font-family: sans-serif;
  }
</style>


# The <span class="uvk">uvk</span> command-line tool

Installing the `uvk` package adds an eponymous utility to the environment,
which we use to install [kernel specs](https://jupyter-client.readthedocs.io/en/5.1.0/kernels.html#kernel-specs)
for <span class="uvk">uvk</span>.

## Kernel specs in a nutshell

Although they were invented in the Python developer community, Jupyter notebooks
are not a Python-specific technology.
Rather, a notebook is a mix of documentation (Markdown) cells and code cells.
The latter contain source code that can be sent to a _kernel_ for execution,
yielding back results that get appended to these cells as the notebook is rendered.
The kernel is a distinct process that speaks with the Jupyter server-side application
through a dedicated [protocol](https://github.com/jupyter/jupyter/wiki/Jupyter-kernels). 

When the user opens a notebook, Jupyter looks up the notebook's metadata and retrieves
the name of the notebook's [kernel spec](https://jupyter-client.readthedocs.io/en/5.1.0/kernels.html#kernel-specs).
Kernel specs consist in metadata that Jupyter uses to know how to start a kernel appropriate
to the notebook's code cells, as well as how to support the editing of these cells.
These kernel specs are stored in the Jupyter [data directories](https://docs.jupyter.org/en/stable/use/jupyter-directories.html#data-files),
under the `kernels` subdirectory.
The purpose of the `uvk` command-line tool is to add the <span class="uvk">uvk</span> kernel spec
to one of these directories,
with some customizable settings.

## Parallel with IPython kernel installation

Since <span class="uvk">uvk</span> is, in essence, a wrapper around the IPython kernel,
it makes sense to coordinate the semantics of the kernel installer with those of the
IPython kernel.
As such, any command line argument of the `uvk` utility that has a counterpart in the invocation
of `python -m ipykernel install` may be expected to induce a similar behaviour.

## Kernel spec installation location

The `uvk` utility, like `ipykernel install` may be called without any command line argument
in principle.
This deploys the kernel spec in the main *system* Jupyter data directory.

```sh
uvk  # Just like bare python -m ipykernel install
```

Common practice makes it much more common, nowadays, to deploy Jupyter systems within
virtual environments, rather than in global system spaces.
The way to target the environment's Jupyter data directory is the `--sys-prefix` boolean argument.

```sh
uvk --sys-prefix
```

In Jupyterhub systems, even the Jupyter system's environment is not writable by the user.
<a id="user"></a>
One may, however, add kernel specs to their specific *user* Jupyter data directory, using
the `--user` boolean argument.

```sh
uvk --user
```

It is equally possible to deploy the <span class="uvk">uvk</span> kernel spec in the Jupyter
data directory of an arbitrary environment whose [prefix directory](https://docs.python.org/3/using/configure.html#cmdoption-prefix)
we know.

```sh
uvk --prefix /prefix/directory/of/environment
```

## Kernel spec denomination

A kernel spec is identified by Jupyter and other tools by its *name*, which is typically written
like an filesystem path, avoiding blanks and typographical sigils.
It is presented to the user with a distinct readable label, called the *display name*,
which is written with spaces and characters that facilitate readability.
Either of these is specified with the `--name` and `--display-name` arguments.

```sh
uvk --name my_own_uvk --display-name "Bespoke uvk kernel"
```

## IPython kernel attributes and settings

`uvk` reflects the setting of environment variables in the IPython kernel it wraps around:
`--env` arguments behave just like `--env` arguments to `ipykernel install`.
The following examples sets up the kernel so it may be used to develop [AnyWidget](https://anywidget.dev/)
widgets with [hot module reloading enabled](https://anywidget.dev/blog/anywidget-02/).

```sh
uvk --name anywidget_livereload --env ANYWIDGET_HMR 1
```

<a id="python-version"></a>
One of uv's most powerful features is its ability to flip between multiple distinct Python stacks.
This is highly useful for library developers who attempt to support all of the five
minor Python versions [in living support](https://devguide.python.org/versions/) at any given moment.
The `-p/--python` option is reflected over to the `uv` invocation that wraps around the IPython
kernel launch.

```sh
uvk --name python3.11 --display-name "uvk Python 3.11" --python 3.11
uvk --name native --display-name "uvk native" --python /usr/bin/python
```

## Miscellanea

| Option           | Summary                                          |
|:-----------------|:-------------------------------------------------|
| `uvk --help`     | Online help.                                     |
| `uvk -q/--quiet` | Quieter output.                                  |
| `uvk -qq`        | Even quieter output.                             |
| `uvk -qqq`       | If it says _anything_, you should pay attention. |
| `uvk --debug`    | Debugging trace output.                          |
