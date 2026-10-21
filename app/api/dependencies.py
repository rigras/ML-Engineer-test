"""Dependency providers: hand the composition root's objects to routers (CONSTITUTION §4.5).

The ``Container`` is built once in the lifespan (``app/main.py``) and stored on
``app.state``; providers only read it — they never construct anything.
"""

from dataclasses import dataclass
from typing import cast

from fastapi import Request


@dataclass(frozen=True)
class Container:
    """Everything the API layer needs, already wired by the composition root."""


def get_container(request: Request) -> Container:
    """Return the container the lifespan stored on the app."""
    return cast(Container, request.app.state.container)
