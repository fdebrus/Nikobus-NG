"""The texts of the options menu, in the three languages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import SetupFixture

_TRANSLATIONS = Path(__file__).parent.parent / "custom_components" / "nikobus_ng" / "translations"
_LANGUAGES = ("en", "fr", "nl")
_NOT_IN_EVERY_MENU = {"files", "take_over", "give_back"}


def _texts(language: str) -> dict[str, Any]:
    texts: dict[str, Any] = json.loads((_TRANSLATIONS / f"{language}.json").read_text(encoding="utf-8"))
    return texts


def _keys(node: Any, path: str = "") -> set[str]:
    if not isinstance(node, dict):
        return {path}
    return {key for name, child in node.items() for key in _keys(child, f"{path}/{name}")}


@pytest.mark.parametrize("language", _LANGUAGES[1:])
def test_a_language_has_the_keys_of_english(language: str) -> None:
    assert _keys(_texts(language)) == _keys(_texts("en"))


@pytest.mark.parametrize("language", _LANGUAGES)
async def test_every_entry_of_the_options_menu_says_what_it_is_for(
    hass: HomeAssistant, setup: SetupFixture, entry: MockConfigEntry, language: str
) -> None:
    await setup()
    menu = await hass.config_entries.options.async_init(entry.entry_id)
    hass.config_entries.options.async_abort(menu["flow_id"])
    offered = list(menu["menu_options"])
    # The simulated installation has an inventory and nothing to take over.
    assert offered == ["names", "outputs", "shutter", "led_key", "gateway", "module_type"]

    init = _texts(language)["options"]["step"]["init"]
    assert init["description"]
    assert set(init["menu_options"]) == set(offered) | _NOT_IN_EVERY_MENU
    assert set(init["menu_option_descriptions"]) == set(init["menu_options"])
    assert all(init["menu_option_descriptions"].values())
