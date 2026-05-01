# The `uvk` command-line tool

Installing the `uvk` package adds an eponymous utility to the environment,
which we use to install additional [kernel specs](https://jupyter-client.readthedocs.io/en/5.1.0/kernels.html#kernel-specs)
for <span class="uvk">uvk</span>,
as well as launch the kernel.

## <a id="install"></a>Installing <span class="uvk">uvk</span> kernel specs

This is done with the `uvk install` command.

### Kernel specs in a nutshell

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

### Parallel with IPython kernel installation

Since <span class="uvk">uvk</span> is, in essence, a wrapper around the IPython kernel,
it makes sense to coordinate the semantics of the kernel installer with those of the
IPython kernel.
As such, almost every command line argument of the `uvk` utility that has a counterpart in the invocation
of `python -m ipykernel install` that may be expected to induce a similar behaviour.

### Kernel spec installation location

The `uvk` utility, like `ipykernel install` may be called without any command line argument
in principle.
This deploys the kernel spec in the main *system* Jupyter data directory.

```sh
uvk install  # Just like bare python -m ipykernel install
```

Common practice makes it much more common, nowadays, to deploy Jupyter systems within
virtual environments, rather than in global system spaces.
The way to target the environment's Jupyter data directory is the `--sys-prefix` boolean argument.

```sh
uvk install --sys-prefix
```

In Jupyterhub systems, even the Jupyter system's environment is not writable by the user.
<a id="user"></a>
One may, however, add kernel specs to their specific *user* Jupyter data directory, using
the `--user` boolean argument.

```sh
uvk install --user
```

It is equally possible to deploy the <span class="uvk">uvk</span> kernel spec in the Jupyter
data directory of an arbitrary environment whose [prefix directory](https://docs.python.org/3/using/configure.html#cmdoption-prefix)
we know.

```sh
uvk install --prefix /prefix/directory/of/environment
```

### Kernel spec denomination

A kernel spec is identified by Jupyter and other tools by its *name*, which is typically written
like an filesystem path, avoiding blanks and typographical sigils.
It is presented to the user with a distinct readable label, called the *display name*,
which is written with spaces and characters that facilitate readability.
Either of these is specified with the `--name` and `--display-name` arguments.

```sh
uvk install --name my_own_uvk --display-name "Bespoke uvk kernel"
```

### IPython kernel attributes and settings

`uvk` reflects the setting of environment variables in the IPython kernel it wraps around:
`--env` arguments behave just like `--env` arguments to `ipykernel install`.
The following examples sets up the kernel so it may be used to develop [AnyWidget](https://anywidget.dev/)
widgets with [hot module reloading enabled](https://anywidget.dev/blog/anywidget-02/).

```sh
uvk install --name anywidget_livereload --env ANYWIDGET_HMR 1
```

Another kernel attribute can be set up in order to start a *development version* of
<span class="uvk">uvk</span>, rather than a production version available on a remote package index.
The user of such kernels is expected to have cloned the
<span class="uvk">uvk</span> [Git repository](https://github.com/hamelin/uvk.git)
to their local machine &mdash; let's say at path `$HOME/work/uvk`.
To install a kernel that uses the code out of this local repository,
use the `--dev` option.

```sh
uvk install --name uvk-dev --display-name "uvk @ work/ [dev]" --dev $HOME/work/uvk
```

### Miscellanea

| Option           | Summary                                           |
|:-----------------|:--------------------------------------------------|
| `uvk --help`     | Online help.                                      |
| `uvk -q/--quiet` | Quieter output.                                   |
| `uvk -qq`        | Even quieter output.                              |
| `uvk -qqq`       | If it says _anything_, you should pay attention.  |
| `uvk --debug`    | Debugging trace output. Very useful with `--dev`! |


## <a id="launch"></a>Launching a <span class="uvk">uvk</span> kernel

The `uvk launch` command is mainly used by the Jupyter system when opening notebooks and consoles.
Unless one develops their own Jupyter applications and devices,
one is unlikely to run it themselves from their shell.

`uvk launch` is responsible for detecting if the kernel is started for a notebook,
and if so,
to locate and grab its inline script metadata snippet.
Once it has done so,
it prepares a IPython kernel launch script with this metadata,
and leans on **uv** to run it in an isolated, duly prepared environment.

Like the `ipykernel_launcher` module that comes with the IPython kernel,
`uvk launch` takes one option, `-f`, that should specify a JSON file carrying
data on how Jupyter expects to connect to the new kernel.
`uvk launch` simply relays this file to the IPython kernel;
look at the latter's [documentation](https://ipykernel.readthedocs.io/en/stable/api/ipykernel.html#ipykernel.kernelapp.IPKernelApp)
for (minute) details.
