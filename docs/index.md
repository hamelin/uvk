<div style="display: flex; flex-flow: row nowrap; justify-content: flex-start; align-items: center; gap: 10pt;">
<div style="flex: 0 1 content; width: 1in;">
  <img src="images/logo.svg"/>
</div>
<div style="flex: 1 1;">
<h1><span style="color: orange;">uvk:</span> Fully-isolated IPython kernel through uv</h1>
</div>
</div>

This tool starts Jupyter IPython kernels ([ipykernel](https://pypi.org/project/ipykernel/))
in ad hoc isolated environments built on-the-fly very quickly using [uv](https://pypi.org/project/ipykernel/).
The uvk kernel comes with an IPython extension that provides magics to
specify the package dependencies on which the notebook relies.
These packages are installed in the isolated environment as these magics are
executed, and the ad hoc virtual environment is discarded when the kernel is shut down.

## Quickstart

The following examples assume one just created and activated a virtual environment
in which to run.

### 1. Set up

As a shared workstation administrator, deploy uvk with Jupyterhub:

```sh
pip install jupyterhub jupyterlab uvk  # Includes uv
uvk                                    # Provide global access to the uvk kernelspec
jupyterlab
```

As a Jupyterhub user, deploy uvk out of the current environment:

```sh
pip install uvk
uvk --user  # Add the uvk kernelspec as user-specific
# Just wait for the uvk icon to appear in the Launcher.
```

From a Linux/MacOS shell, with uv installed, run Jupyter Lab with Python
kernels managed with uvk:

```sh
uv run --with=jupyterlab --with=uvk $SHELL <<SCRIPT
uvk --sys-prefix
jupyter lab
SCRIPT
```

### 2. In a notebook

```ipython
%python_version >=3.13
```

```ipython
%%dependencies
duckdb
ipywidgets
matplotlib
scikit-learn>=1.8
toponymy
umap-learn>=0.5.10
```

## Why use this?

<style>
  .twocol {
    display: grid;
    grid-template:
      [header] "." auto [end-header]
      "." 8pt
      [text] "." auto [end-text]
      / [jupyterhub] 1fr [gap] 16pt [selfcontained] 1fr [end];
    width: 100%;
  }

  .twocol-header {
    grid-row: header;
    font-weight: bold;
  }

  .twocol-jupyterhub {
    grid-column: jupyterhub;
  }

  .twocol-text {
    grid-row: text;
  }

  .twocol-selfcontained {
    grid-column: selfcontained;
  }
</style>
<div class="twocol">
  <div class="twocol-header twocol-jupyterhub">
    Improved flexibility in Jupyterhub workstations
  </div>
  <div class="twocol-text twocol-jupyterhub">
    <p>
      When one needs packages that are not part of the default Jupyterhub
      kernel, one typically builds one's own environments and then install
      <a href="https://docs.jupyter.org/en/latest/projects/kernels.html">kernelspecs</a>
      respectively tied to each of these environments.
      This is a clumsy approach: the notebooks authored against each of these
      environment-specific kernels store that kernel's identification.
      In order to share these notebooks,
      either one must share complicated instructions for deploying kernels
      named per their own environments,
      or one must guide their users through choosing a new kernel, presumably
      the default IPython kernel, the first time they open the shared
      notebook. (In this latter case,
      the notebook is modified by this new kernel setting,
      padding eventual diff hunks with spurious metadata changes.)
    </p>
    <p>
      With uvk, additional package requirements are encoded into the notebook,
      whose kernel gets set as <strong>uvk</strong>.
      Standalone notebooks specify these requirements similarly to
      <a href="https://packaging.python.org/en/latest/specifications/inline-script-metadata/">script
      metadata</a> (as uv can leverage to isolate a <a href="https://packaging.python.org/en/latest/specifications/inline-script-metadata/">script's
      dependencies</a>).
      Notebooks that belong to projects can grab dependencies off of the those
      projects' <samp>pyproject.toml</samp>.
      In all cases, no explicit environment nor kernelspec need to be
      created, managed nor cleaned up by the user.
    </p>
  </div>
  <div class="twocol-header twocol-selfcontained">
    Authoring self-contained notebooks
  </div>
  <div class="twocol-text twocol-selfcontained">
    <p>
      Since Jupyter notebooks have been around,
      they posed the tantalizing possibility of sharing them
      <em>by themselves</em>.
      However,
      most Jupyter users lean on a panoply of nonstandard package
      dependencies. Notebooks starting with a `%pip` magic to fetch these
      dependencies require the reader running the notebook to ensure this
      setup occurs in an isolated environment <em>they</em> must set up
      themselves. Even if notebook authors share metadata
      (e.g. <samp>requirements.txt</samp>)
      to set up the environment, the reader remains on the hook to host and
      manage the environment. How rude!
      <!--
      Some communities manage to collaborate more easily through some
      environments shared ahead of time by convention (using platforms like
      Jupyterhub), and thus may exchange
      notebooks more easily through such collaboration tools as
      <a href="https://github.com/nbgallery/nbgallery">NBGallery</a>.
      This author's experience within such communities is that some authors
      invariably require something that is not part of shared environment,
      and uses some <samp>%pip install</samp> that pollute the readers'
      environment (under a reasonable assumption that it can be easily reset
      to its original state).
      -->
    </p>
    <p>
      uvk fills this gap by starting the IPython kernel process through a
      <samp>uv run --isolated</samp> command line.
      This instantiates a virtual environment on the fly, which can be
      modified harmlessly with <samp>%pip install</samp> and similar
      statements. In addition, the magics of the <a href="reference/">uvk
      IPython extension</a> leverage the very fast package deployment tooling
      provided by uv. The outcome is no-touch, transparent computation
      isolation traded off for a very small redeployment cost on each kernel
      start-up.
    </p>
  </div>
</div>
