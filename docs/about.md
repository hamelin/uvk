<style>
  span.uvk {
    font-family: sans-serif;
  }
</style>

# About <span class="uvk">uvk</span>

<span class="uvk">uvk</span> is a wrapper around the [Ipython Jupyter kernel](https://ipykernel.readthedocs.io/en/stable/)
that launches it through the [uv](https://docs.astral.sh/uv/) package and project manager.
uv is spectacularly fast and <span class="uvk">uvk</span> leans on its ability to run
Python processes in ad hoc isolated virtual environments.

## Custom user environments on Jupyterhub

Many organizations will share workstations or compute clusters using [Jupyterhub](https://jupyter.org/hub),
a Jupyter interface spawning system deployed on top of various authentication and compute orchestration
systems.
Users of such computing platforms are provided with a Python computing environment that may
lack some packages they would use.

In certain cases, the incumbent environment is modifiable by the user,
being set up on the fly when starting, say,
a Kubernetes node to run their [single-user server](https://jupyterhub.readthedocs.io/en/stable/explanation/concepts.html#single-user-notebook-server).
Most users then `pip install` any further package they require,
sometimes overriding packages deployed in the incumbent environment (or their dependencies),
resulting in surprise breakage when these users start computing.

In other cases, the default environment cannot be modified,
but users may then build their own virtual environments and spin off tied Python kernels.
Managing these environments and their kernels require coordinating two suites of tools and
artifacts (`python -m venv` and `pip` to manage virtualenvs on the one hand,
and `jupyter` and `ipykernel install` to manage Jupyter [kernel specs](https://jupyter-client.readthedocs.io/en/5.1.0/kernels.html#kernel-specs)
on the other hand),
a task somewhat tedious and awkward.
In addition, these user-specific kernel specs get _their own name_.
If the author of a notebook using such a bespoke kernel [shares it](#self-contained-notebooks),
even with another user of the same Jupyterhub platform,
the recipient will open the notebook to a strange dialog asking them to _choose a distinct kernel_,
as the one named in the notebook does not exist in their own environment.
The whole user experience is, again, unduly awkward.

<span class="uvk">uvk</span> addresses both aspects of the problem by running
kernel processes in fully isolated virtualenvs instantiated on the fly,
and managed without user intervention. 
These virtual environments start out with a bare-bones Python/IPython stack,
but users can `%uv pip install` any package they require.
The incumbent Python environment provided through the single-user server spawn remains unaffected.
The aggressive caching strategies and sheer performance of uv at deploying packages in these
environments mitigates any presumed inefficiency one may presume from under-the-hood
repetitive package wrangling.
The system as a whole works nearly as fast as fixed virtualenvs.

## Self-contained notebooks

Jupyter notebooks are more than mere computing vehicles:
they are a successful embodiment of [literate programming](https://en.wikipedia.org/wiki/Literate_programming),
enabling an author to describe or comment a computation and execute it in turns;
and their audience to perform and examine the results of each step at the pace
they choose.
Notebook authors, however,
must overcome the the problem that their audience might not have at hand all the software
their notebook relies on.

In certain notebook sharing communities,
authors blithely start their notebooks with `%pip install` statements,
asserting their requirements with more or less clobbering force against the
reader's current Python environment.
More often, notebooks simply cannot be shared without a panoply of metadata
stating the requirements (such as `requirements.txt` usable by Pip,
or the more versatile `pyproject.toml`, or anything out of _countless_ concurrent
project management tools for Python),
along with instructions for standing up an environment in which to set up
these requirements, along with yet another install of the Jupyter stack.
Such instructions must be silently translated and, all too often,
transcribed by people using any variation from the standalone Jupyter Lab
setup, such as [Jupyterhub users](#custom-user-environments-on-jupyterhub).

<span class="uvk">uvk</span> addresses this problem by automatically providing
an isolated runtime environment for a notebook authored against it.
<span class="uvk">uvk</span> further provides an IPython kernel [extension](reference/uvk_ext.md)
through which an author can elegantly express the requirements the kernel process
(and, in certain respects, the environment that spawned it) must satisfy.
The user does not have to guard against spurious modifications to the environment
that spawned their Jupyter instance.
Once the notebook has been executed and the user shuts it down,
the environment is automatically dismantled.
Thus, notebooks authored to use the <span class="uvk">uvk</span> kernel directly
can be shared without any other accompanying artifact:
they become self-contained executable documents.
They can be pre-rendered in some [Github Gist](https://gist.github.com/),
from where interested can download them to their own computer for further study.
