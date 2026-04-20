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

Let's assume you run a Jupyter Lab or Notebook instance is from your own computer;
[see here](install.md#jupyterhub-setup) for using <span class="sans">uvk</span> on
Jupyterhub.
First off, deploy the <span class="sans">uvk</span> kernel where Jupyter can see it.
*(Wait, what's [uvx](https://docs.astral.sh/uv/concepts/tools/)?)*

| Operating system                      | Quickstart command |
|:--------------------------------------|:-------------------|
| Microsoft Windows                     | `uvx --from=jupyterlab --with=uvk cmd /c "uvk --sys-prefix && jupyter lab"` |
| MacOS, GNU/Linux,<br>\*BSD, UNIX etc. | `uvx --from=jupyterlab --with=uvk $SHELL -c "uvk --sys-prefix && jupyter lab"` |`

Now run through the [tutorial notebook](Tutorial.ipynb) to see what this kernel can do for you.

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
    Shared workstations fronted with <a href="https://jupyter.org/hub">Jupyterhub</a>
    will provide some reasonable base computing environment,
    but building one's own custom environment requires awkward management of
    virtual environments and associated Jupyter kernels.
    <span class=sans>uvk</span> completely mitigates these difficulties.</span>
    <a href="about/#custom-user-environments-on-jupyterhub">Read further</a>
  </div>
  <div class="selfcontained">
    In the most general sense, Jupyter notebook are not <em>self-contained</em>
    computing artifacts.
    Sharing notebooks require adding them to a group of metadata files that
    facilitate recreating the computing environment they can run in
    (such as <samp>requirements.txt</samp>).
    <span class=sans>uvk</span> provides elegant means to embed this metadata
    as part of the notebook,
    enabling their self-contained execution on a <span class=sans>uvk</span>
    kernel anywhere else.
    <a href="about/#self-contained-notebooks">Read further</a>
  </div>
</div>

## Going further

- [About <span class="sans">uvk</span>](about.md)
- Full [installation](install.md) instructions
- [Tutorial](Tutorial.ipynb)
- [How to?](howto/index.md) recipes and [notebook examples](https://github.com/hamelin/uvk/examples/)
- [Deep dives](deepdives/index.md) into the details
- [Tool and API reference](reference/index.md)

Copyright 2026 Benoit Hamelin.
