"""Command palette provider for rip scripts."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from textual.command import DiscoveryHit, Hit, Hits, Provider

from .favorites import get_script_priority, is_favorite_macro
from .macros import list_macros

if TYPE_CHECKING:
    from .app import RiptextApp
    from .core.models import ScriptMetadata


def _script_group(script: "ScriptMetadata") -> str:
    priority = get_script_priority(script.slug)
    if priority[0] == 0:
        return "Favorites"
    if priority[2] < 999:
        return "Recent"
    return script.category


def _script_display(script: "ScriptMetadata") -> str:
    group = _script_group(script)
    if group in {"Favorites", "Recent"}:
        return f"{group}: [{script.category}] {script.name}"
    return f"{group}: {script.name}"


def _script_help(script: "ScriptMetadata") -> str | None:
    parts = []
    if script.description:
        parts.append(script.description)
    if script.tags:
        parts.append(f"Tags: {', '.join(script.tags)}")
    if script.aliases:
        parts.append(f"Aliases: {', '.join(script.aliases)}")
    return " | ".join(parts) or None


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
            yield DiscoveryHit(
                display=_script_display(script),
                command=partial(app.run_script, script),
                help=_script_help(script),
            )

        # Macros
        macros = list_macros()
        macros.sort(
            key=lambda macro: (
                0 if is_favorite_macro(macro["slug"]) else 1,
                macro["name"].lower(),
            )
        )
        for macro in macros:
            prefix = "★ " if is_favorite_macro(macro["slug"]) else ""
            steps = app.macro_step_summary(macro["slugs"])
            yield DiscoveryHit(
                display=f"{prefix}Macro: {macro['name']}",
                command=partial(app.run_saved_macro, macro),
                help=f"Steps: {steps}",
            )
            yield DiscoveryHit(
                display=f"Macros: Preview {macro['name']}",
                command=partial(app.preview_macro, macro),
                help=f"Steps: {steps}",
            )
            yield DiscoveryHit(
                display=f"Macros: Rename {macro['name']}",
                command=partial(app.prompt_rename_macro, macro),
                help="Rename this saved macro",
            )
            favorite_verb = (
                "Unfavorite" if is_favorite_macro(macro["slug"]) else "Favorite"
            )
            yield DiscoveryHit(
                display=f"Macros: {favorite_verb} {macro['name']}",
                command=partial(app.toggle_saved_macro_favorite, macro),
                help="Toggle macro favorite status",
            )
            yield DiscoveryHit(
                display=f"Macros: Delete {macro['name']}",
                command=partial(app.delete_saved_macro, macro),
                help="Delete this saved macro",
            )

        for entry in app.transform_history_for_commands():
            yield DiscoveryHit(
                display=f"History: Re-run {entry.label}",
                command=partial(app.rerun_history_entry, entry),
                help=f"Steps: {app.macro_step_summary(entry.slugs)}",
            )

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        app = self._app()

        for script in app.scripts_for_commands():
            candidate = " ".join(
                [
                    script.name,
                    script.slug,
                    script.description,
                    " ".join(script.tags),
                    " ".join(script.aliases),
                    script.category,
                ]
            ).strip()
            score = matcher.match(candidate)
            if score <= 0:
                continue
            # Boost favorites and recent in search results
            fav_rank = get_script_priority(script.slug)
            if fav_rank[0] == 0:
                score += 20  # favorite boost
            elif fav_rank[2] < 999:
                score += 10  # recent boost

            yield Hit(
                score,
                matcher.highlight(_script_display(script)),
                partial(app.run_script, script),
                help=_script_help(script),
            )

        # Macros
        for macro in list_macros():
            steps = app.macro_step_summary(macro["slugs"])
            candidate = f"macro {macro['name']} {' '.join(macro['slugs'])} {steps}"
            score = matcher.match(candidate)
            if score > 0:
                if is_favorite_macro(macro["slug"]):
                    score += 20
                prefix = "★ " if is_favorite_macro(macro["slug"]) else ""
                yield Hit(
                    score,
                    matcher.highlight(f"{prefix}Macro: {macro['name']}"),
                    partial(app.run_saved_macro, macro),
                    help=f"Steps: {steps}",
                )

            favorite_verb = (
                "unfavorite" if is_favorite_macro(macro["slug"]) else "favorite"
            )
            favorite_display = favorite_verb.title()
            action_hits = [
                ("preview", f"Macros: Preview {macro['name']}", app.preview_macro),
                ("rename", f"Macros: Rename {macro['name']}", app.prompt_rename_macro),
                (
                    favorite_verb,
                    f"Macros: {favorite_display} {macro['name']}",
                    app.toggle_saved_macro_favorite,
                ),
                ("delete", f"Macros: Delete {macro['name']}", app.delete_saved_macro),
            ]
            for action, display, callback in action_hits:
                action_score = matcher.match(f"{action} macro {macro['name']} {steps}")
                if action_score <= 0:
                    continue
                yield Hit(
                    action_score,
                    matcher.highlight(display),
                    partial(callback, macro),
                    help=f"Steps: {steps}",
                )

        for entry in app.transform_history_for_commands():
            steps = app.macro_step_summary(entry.slugs)
            score = matcher.match(f"history rerun {entry.label} {steps}")
            if score <= 0:
                continue
            yield Hit(
                score,
                matcher.highlight(f"History: Re-run {entry.label}"),
                partial(app.rerun_history_entry, entry),
                help=f"Steps: {steps}",
            )
