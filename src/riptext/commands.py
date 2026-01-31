"""Command palette provider for rip scripts."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from textual.command import DiscoveryHit, Hit, Hits, Provider

if TYPE_CHECKING:
    from .app import RiptextApp


class RipCommandProvider(Provider):
    """Provide rip scripts to the command palette."""

    def _app(self) -> "RiptextApp":
        from .app import RiptextApp

        app = self.app
        assert isinstance(app, RiptextApp)
        return app

    async def discover(self) -> Hits:
        app = self._app()
        for script in app.scripts_for_commands():
            yield DiscoveryHit(
                display=script.name,
                command=partial(app.run_script, script),
                help=script.description or None,
            )

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        app = self._app()

        for script in app.scripts_for_commands():
            candidate = " ".join(
                [script.name, script.slug, script.description, " ".join(script.tags)]
            ).strip()
            score = matcher.match(candidate)
            if score <= 0:
                continue
            yield Hit(
                score,
                matcher.highlight(script.name),
                partial(app.run_script, script),
                help=script.description or None,
            )
