from contextlib import contextmanager
from typing import Protocol

from reactivity import create_effect
from rich.console import RenderableType
from rich.live import Live


class UI(Protocol):
    def render(self) -> RenderableType: ...


@contextmanager
def rendering(ui: UI):
    with Live() as live, create_effect(lambda: live.update(ui.render(), refresh=True)):
        yield
