"""Output dialects — ``obsidian`` | ``plain``. (``logseq`` deferred post-launch.)

The flavor controls how *our* generated links are written: Obsidian uses
wikilinks; plain uses portable Markdown links. Untrusted transcript content is
neutralized in the formatter regardless of flavor.
"""

from __future__ import annotations


class Flavor:
    """Base dialect. ``link`` renders an internal link to another note."""

    name: str = "plain"
    obsidian: bool = False

    def link(self, target_stem: str, alias: str | None = None) -> str:
        raise NotImplementedError


class ObsidianFlavor(Flavor):
    name = "obsidian"
    obsidian = True

    def link(self, target_stem: str, alias: str | None = None) -> str:
        if alias and alias != target_stem:
            return f"[[{target_stem}|{alias}]]"
        return f"[[{target_stem}]]"


class PlainFlavor(Flavor):
    name = "plain"
    obsidian = False

    def link(self, target_stem: str, alias: str | None = None) -> str:
        return f"[{alias or target_stem}]({target_stem}.md)"


_FLAVORS: dict[str, Flavor] = {"obsidian": ObsidianFlavor(), "plain": PlainFlavor()}


def get_flavor(name: str) -> Flavor:
    """Return the flavor by name, falling back to ``plain`` for unknown names."""
    return _FLAVORS.get(name, _FLAVORS["plain"])
