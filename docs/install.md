<style>
  span.uvk {
    font-family: sans-serif;
  }
</style>


# Installing

## Standalone Jupyter setup

Many people use [Jupyter Lab](https://jupyterlab.readthedocs.io/en/latest/) or
[Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/latest/) on their own
workstation or computer.
The following instructions are for installing <span class="uvk">uvk</span> in
a Python environment where either Jupyter Lab or Notebook gets set up.
**They all assume the user types commands in a shell terminal.**

### Using `venv` and Pip

Let's build and set up a virtualenv named `jupyter` right in the shell's current directory.


```sh
python -m venv jupyter
```
  
[Activating](https://docs.python.org/3/library/venv.html#how-venvs-work)
this environment depends on the operating system and shell one is using.
Here are instructions for the most common situations:

| Operating system                   | Shell                        | Activation command |
|:-----------------------------------|:-----------------------------|:-------------------|
| Windows                            | Classic command prompt (CMD) | `.\jupyter\Scripts\activate.bat` |
|                                    | Powershell                   | `.\jupyter\Scripts\Activate.ps1` |
| UNIX-ish                           | Bash or Zsh                  | `. jupyter/bin/activate` |
|                                    | Fish                         | `source jupyter/bin/activate.fish` |
|                                    | Nushell                      | `overlay use jupyter/bin/activate.nu` |

!!! note "UNIX-ish (adj.)"
    Refers to all UNIX-descended or UNIX-imitating operating systems in used commonly to drive
    modern workstations. Covers GNU/Linux distributions, \*BSD and MacOS &mdash;
    all tier-1 and tier-2 [uv-supported](https://docs.astral.sh/uv/reference/policies/platforms/)
    platforms.

Now install Jupyter Lab or Jupyter Notebook and <span class="uvk">uvk</span>.
and install the <span class="uvk">uvk</span> kernel spec so that Jupyter Lab sees it.

```sh
pip install jupyterlab notebook uvk
uvk --sys-prefix
```

From there, start Jupyter Lab or Notebook:

```sh
jupyter lab  # or jupyter notebook
```

and one should see the <span class="uvk">uvk</span> kernel icon to start authoring a notebook
against it.

<a id="screenshot-jupyterlab"></a>
![Screenshot of Jupyter Lab with uvk kernel](images/screenshot-jupyterlab-uvk.png)

### Using Conda

We build a Conda environment named `jupyter` in which to install Jupyter Lab/Notebook.
The activation of this environment is not dictated by operating system or shell.
However, we must still use Pip to install <span class="uvk">uvk</span>,
as it is not distributed as a Conda package.

```sh
conda create -n jupyter --yes jupyter jupyterlab
conda activate jupyter
pip install uvk
uvk --sys-prefix
jupyter lab
```

You should then expect to see a browser window or tab open with a screen similar to [above](#screenshot-jupyterlab).

### Using `uv tool install`

The most elegant installation approach for uv users is [`uv tool install`](https://docs.astral.sh/uv/concepts/tools/#the-uv-tool-interface),
putting <span class="uvk">uvk</span> in the same [tool environment](https://docs.astral.sh/uv/concepts/tools/#tool-environments)
as the complete suite of common Jupyter tools.

!!! hint "Enabling one's shell to use uv-installed tools"
    `uv tool install` adds executables in a directory that must be put in one's `PATH`
    environment variable in order to call them from one's shell.
    The easiest way to do this is to run

    `uv tool update-shell`

    and then restart the shell.

Run the following:

```sh
uv tool install jupyter-core --with=jupyter --with-executables-from=uvk
```

Now your shell has the `uvk` executable,
which sees itself as part of the same tool environment as the Jupyter tools.
Now run

```sh
uvk --sys-prefix
```

to install the <span class="uvk">uvk</span> kernel.
Running Jupyter

```sh
jupyter lab
```

is all it takes now to enjoy the kernel from everywhere the `jupyter` executable is not
clobbered.

## Jupyterhub setup as administrator

[Jupyterhub](https://jupyter.org/hub) is a common system for sharing a workstation or compute
cluster by spawning Jupyter Lab instances to multiple users,
deployed over a authentication and compute orchestration subsystems.
The <span class="uvk">uvk</span> kernel is particularly useful on such systems to facilitate 
access to bespoke sets of requirements.

<span class="uvk">uvk</span> provides the greatest benefits when it is made available to the
Jupyterhub instance out of the box, as part of the environment provided through the Jupyterhub
install.
Since the simplest way to install Jupyterhub is through PyPI,
we demonstrate the installation of <span class="uvk">uvk</span> in the same environment.
We also assume deployment on a UNIX-ish system.
Administrators may look up other examples on this page to adapt the instructions.

```sh
python -m venv ./jupyterhub
. jupyterhub/bin/activate
pip install jupyterhub uvk
uvk --sys-prefix
```

The Jupyterhub system then includes the <span class="uvk">uvk</span> kernel side by side with the
default IPython kernel.

## _User_ <span class="uvk">uvk</span> kernel showing up in any Jupyter instance

The <span class="uvk">uvk</span> kernel can be installed in the _user_ data directory that
Jupyter looks up when searching for kernel specs.
That way, the kernel shows up in every Jupyter Lab or Notebook instance one runs,
including on Jupyterhub.
**This is how a Jupyterhub user can install <span class="uvk">uvk</span> for themselves,
without administrator intervention.**

If **uv** is available,

```sh
uvx uvk --user
```

is all that's needed.
Otherwise, if only Python is present,
building a permanent virtual environment is necessary.

```sh
python -m venv .uvk
. .uvk/bin/activate
pip install uvk      # Comes with uv!
uvk --user
deactivate           # So other env modifications don't modify this one.
```

The environment activation statement in the snippet above varies depending on one's shell.
Look up [here](#using-venv-and-pip) if you use neither `bash` nor `zsh`.

If the Jupyter instance where the kernel is expected is already running
(e.g. as on Jupyterhub),
the user should see the <span class="uvk">uvk</span> icon appear in the Launcher window
within about a minute of invoking `uvk --user`.
Newly started Jupyter instances will have it from the get-go.

## Comparing the installation of regular IPython kernel specs to `uvk`

Jupyter instances all come with a pre-deployed IPython kernel,
named by default **Python 3 (ipykernel)**.
Users can add their own IPython kernels,
typically in order to use their own environments in Jupyter kernels.
Such kernels get an *identifier name* and a *display name*:
the former is for tracking the kernel spec by tools,
and the latter is used to label the kernel spec in the Jupyter interface.

```sh
python -m ipykernel install --name mykernel --display-name 'My kernel from my env'
```

The `uvk` executable serves the same purpose as the `ipykernel install` program.
It also takes the same parameters.

```sh
uvk --name my_uvk --display-name 'I liuvke this a lot'
```

Invoke `uvk --help` for a terse listing of the command line arguments.
The [full reference](reference/uvk_cli.md) includes further examples.
