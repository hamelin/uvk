<style>
span.sans {
  font-family: sans-serif;
}
</style>

<div style="display: flex; flex-flow: row nowrap; justify-content: flex-start; align-items: center; gap: 10pt;">
<div style="flex: 0 1 content; width: 1in;">
  <img src="images/logo.svg"/>
</div>
<div style="flex: 1 1;">
<h1><span style="font-family: sans-serif; font-size: 2em;">uvk</span><br> Fully-isolated IPython kernel through uv</h1>
</div>
</div>

This tool starts Jupyter IPython kernels ([ipykernel](https://pypi.org/project/ipykernel/))
in ad hoc isolated environments built on-the-fly very quickly using [uv](https://pypi.org/project/ipykernel/).
The <span class="sans">uvk</span> kernel comes with an IPython extension that provides magics to
specify the package dependencies on which the notebook relies.
These packages are installed in the isolated environment as these magics are
executed, and the ad hoc virtual environment is discarded when the kernel is shut down.

## Quickstart

### Step 1: getting <span class="sans">uvk</span> kernels

The following assume basic familiarity with [uvx](https://docs.astral.sh/uv/concepts/tools/).

**On one's own computer, in a terminal**

<style>
  div.grid-commands {
    display: grid;
    grid-template: [unixish] "." 1fr [windows] "." 1fr / [platform] auto [command] 1fr;
    column-gap: 5mm;
    margin-bottom: 1.2em;
  }
  .grid-commands .unixish {
    grid-row: unixish / span 1;
  }
  .grid-commands .windows {
    grid-row: windows / span 1;
  }
  .grid-columns .platform {
    grid-column: platform / span 1;
  }
  .grid-columns .command {
    grid-column: 3 / span 1;
  }
</style>
<div class="grid-commands">
  <div class="unixish platform">UNIX-ish</div>
  <div class="unixish command">
    <code>uvx --from=jupyterlab --with=uvk $SHELL -c "uvk --sys-prefix && jupyter lab"</code>
  </div>
  <div class="windows platform">Windows</div>
  <div class="windows command">
    <code>uvx --from=jupyterlab --with=uvk cmd /c "uvk --sys-prefix && jupyter lab"</code>
  </div>
</div>

**On a Jupyterhub single-user server**

```sh
uvx uvk --user
```

Then just wait for the **uvk (Python 3.xx)** icon to show up on your launcher.

### Step 2: in a notebook with the <span class="sans">uvk</span> kernel, use the <span class="sans">uvk</span> extension to deploy package dependencies

Run a pair of cells to assert the Python interpreter version and packages you need.

```ipython
%load_ext uvk
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
      "." auto
      / [jupyterhub] 1fr [selfcontained] 1fr;
    column-gap: 10mm;
  }

  .twocol .jupyterhub {
    grid-row: 1 / span 1;
    grid-column: jupyterhub / span 1;
  }
  .twocol .selfcontained {
    grid-row: 1 / span 1;
    grid-column: selfcontained / span 1;
  }
</style>
<div class="twocol">
  <div class="jupyterhub">
    Shared workstations fronted with [Jupyterhub](https://jupyter.org/hub)
    will provide some reasonable base computing environment,
    but building one's own custom environment requires awkward management of
    virtual environments and associated Jupyter kernels.
    <span class=sans>uvk</span> completely mitigates these difficulties.</span>
    <a href="about/#custom-user-environments-on-jupyterhub">Read further</a>
  </div>
  <div class="selfcontained">
    In the most general sense, Jupyter notebook are not _self-contained_
    computing artifacts.
    Sharing notebooks require adding them to a group of metadata files that
    facilitate recreating the computing environment they can run in
    (e.g. <samp>requirements.txt</samp>, <samp>pyproject.toml</samp>, etc.).
    <span class=sans>uvk</span> provide elegant means to embed this metadata
    as part of the notebook,
    enabling their self-contained executaion on a <span class=sans>uvk</span>
    kernel anywhere else.
    <a href="about/#self-contained-notebooks">Read further</a>
  </div>
</div>

## Going further

- [About <span class="sans">uvk</span>](about.md)
- Full [installation](install.md) instructions
- [Tutorials](tutorials/index.md)
- [How to?](howto/index.md) recipes and [notebook examples](https://github.com/hamelin/uvk/examples/)
- [Deep dives](deepdives/index.md) into the details
- [Tool and API reference](reference/index.md)

Copyright 2026 Benoit Hamelin.
