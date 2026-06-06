"""Command palette provider for rip scripts."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from textual.command import DiscoveryHit, Hit, Hits, Provider

from .favorites import get_script_priority
from .macros import list_macros

if TYPE_CHECKING:
    from .app import RiptextApp


class RipCommandProvider(Provider):
    """Provide rip scripts to the command palette."""

    def _app(self) -> "RiptextApp":
        from .app import RiptextApp

        app = self.app
        assert isinstance(app, RiptextApp)
        return app

    async def startup(self) -> None:
        """Reload scripts when command palette opens."""
        self._app().reload_scripts()

    async def discover(self) -> Hits:
        app = self._app()
        scripts = app.scripts_for_commands()

        # Sort: favorites first, then recent, then alphabetical
        scripts.sort(key=lambda s: (*get_script_priority(s.slug), s.name.lower()))

        for script in scripts:
            fav_rank = get_script_priority(script.slug)
            prefix = "★ " if fav_rank[0] == 0 else ""
            yield DiscoveryHit(
                display=f"{prefix}[{script.category}] {script.name}",
                command=partial(app.run_script, script),
                help=script.description or None,
            )

        # Macros
        for macro in list_macros():
            yield DiscoveryHit(
                display=f"⚡ Macro: {macro['name']}",
                command=partial(app.run_macro, macro["slugs"]),
                help=f"Chain: {' → '.join(macro['slugs'])}",
            )

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        app = self._app()

        for script in app.scripts_for_commands():
            candidate = " ".join(
                [script.name, script.slug, script.description,
                 " ".join(script.tags), script.category]
            ).strip()
            score = matcher.match(candidate)
            if score <= 0:
                continue
            fav_rank = get_script_priority(script.slug)
            prefix = "★ " if fav_rank[0] == 0 else ""
            # Boost favorites and recent in search results
            if fav_rank[0] == 0:
                score += 20  # favorite boost
            elif fav_rank[2] < 999:
                score += 10  # recent boost

            yield Hit(
                score,
                matcher.highlight(f"{prefix}[{script.category}] {script.name}"),
                partial(app.run_script, script),
                help=script.description or None,
            )

        # Macros
        for macro in list_macros():
            candidate = f"macro {macro['name']} {' '.join(macro['slugs'])}"
            score = matcher.match(candidate)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(f"⚡ Macro: {macro['name']}"),
                    partial(app.run_macro, macro["slugs"]),
                    help=f"Chain: {' → '.join(macro['slugs'])}",
                )
