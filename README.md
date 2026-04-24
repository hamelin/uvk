# **uvk** -- Fully isolated IPython kernels through the magic of uv

This project uses [uv](https://docs.astral.sh/uv/)'s ultrafast package deployment
capabilities and on-the-fly isolated environment composition to run the
[IPython kernel](https://ipython.readthedocs.io/en/stable/install/kernel_install.html)
in a Jupyter instance.

- Notebooks can grab their dependencies and leave neither trouble nor cruft behind
- No need for a whole `pyproject.toml` just to run somebody's notebook once
- Elegantly integrate Jupyter notebooks into **uv**-driven project development workflows

| [Full documentation](https://uvk.readthedocs.io/) | [Tutorial](https://uvk.readthedocs.io/en/latest/Tutorial/) | [IPython extension](https://uvk.readthedocs.io/en/latest/reference/uvk_ext/) | [CLI reference](https://uvk.readthedocs.io/en/latest/reference/uvk_cli/) |
|--|--|--|--|

## Quickstart-and-dirty

| I have **uv** 😎 | I only have Python and Pip |
|:-----------------|:---------------------------|
| `uvx uvk --user` | `python -m venv .uvk \`<br>`    && . ./.uvk/bin/activate \`<br>`    && pip install uvk \`<br>`    && uvk --user`<br> |

If your Jupyter instance is already running, wait up to a minute for it to poll for kernel
specs and discover your new **uvk**.
Otherwise, start Jupyter Lab or Jupyter Notebook.

Check out the [tutorial](https://uvk.readthedocs.io/en/latest/Tutorial/) on how to make the most
of **uvk** features.

## License

**uvk** is distributed as open source software under the [MIT license](LICENSE).

## Help and support

Full documentation is on [ReadTheDocs](https://uvk.readthedocs.io/).
If you can't find any answer to your question after some reasonable foraging,
please [open an issue](/hamelin/uvk/issues/new) and I will provide as much guidance as I can.
Please read and abide by the [code of conduct](CODE_OF_CONDUCT.md)
guiding acceptable behaviour in issue and PR conversations.

## Contributing

Contributions are more than welcome.
If you have ideas for features or projects please get in touch.
Whether code,
example notebooks,
example scripts,
documentation &mdash; all equally valuable,
so please do not presume you cannot provide something useful to this project.
To contribute please fork the project, make your changes and submit a pull request.
We will do our best to work through any issues with you and get your contribution merged in.

The **uvk** project is a proud participant to the [Jupyter](https://jupyter.org/)
software ecosystem.
If this project provides value towards your own work,
please consider contributing to the [Jupyter Foundation](https://jupyterfoundation.org/).
