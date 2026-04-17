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
| UNIX-ish (GNU/Linux, \*BSD, MacOS) | Bash or Zsh                  | `. jupyter/bin/activate` |
|                                    | Fish                         | `source jupyter/bin/activate.fish` |
|                                    | Nushell                      | `overlay use jupyter/bin/activate.nu` |

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

![Screenshot of Jupyter Lab with uvk kernel](images/screenshot-jupyterlab-uvk.png)

### Parallel between the `uvk` executable and IPyKernel

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
The [full reference](reference/uvk_cli.md) includes some more complex examples.
