"""Links said in words, and devices named as the Nikobus integration names them."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import label_registry as lr
from nikobus_connect.discovery import meaning
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nikobus_ng import async_remove_config_entry_device
from custom_components.nikobus_ng.const import DOMAIN
from custom_components.nikobus_ng.describe import _explained
from custom_components.nikobus_ng.llm_api import API_PROMPT

from .conftest import (
    DIMMER,
    ENTRY_ID,
    KEY_DIMMER,
    KEY_ROLLER,
    KEY_SCENE,
    PLATE,
    ROLLER,
    SWITCH,
    SetupFixture,
)
from .test_remaining import _options, _reloaded

KEY_EVENT = "event.bus_push_button_4_control_buttons_n1843b4_key_1c"


async def test_a_scanned_link_is_said_in_words_with_its_values_named(hass: HomeAssistant, scanned: SetupFixture) -> None:
    """The links are the ones the scan read out of the simulated modules."""
    await scanned()
    described = await hass.services.async_call(DOMAIN, "describe", {}, blocking=True, return_response=True)
    outputs = {(o["module"], o["channel"]): o for o in described["outputs"]}
    assert outputs[(DIMMER, 1)]["controlled_by"][0]["links"] == [
        {
            "mode": "M01 (Dim on/off (2 buttons))",
            # The link is on key 1C, an upper key.
            "does": "A short press on this key switches the output on at its last level, holding it dims up; "
            "the lower key of the pair switches off and dims down. Dimming on takes 4 s, dimming off 1 s.",
            "dim_on_time": "4 s",
            "dim_off_time": "1 s",
        }
    ]
    roller = next(k for k in described["keys"] if k["address"] == KEY_ROLLER)["drives"][0]
    assert (roller["module"], roller["run_time"]) == (ROLLER, "30 s")
    assert roller["does"].endswith("The motor runs for 30 s.")
    dimmer = next(k for k in described["keys"] if k["address"] == KEY_DIMMER)["drives"][0]
    assert not {"t1", "t2"} & (roller.keys() | dimmer.keys())
    scene = next(s for s in described["scenes"] if s["address"] == KEY_SCENE)
    recalled = "Light scene: a short press recalls the state stored for this output, a press of more than 3 s stores its present state."
    assert {o["does"] for o in scene["outputs"]} == {recalled}


def test_a_link_there_are_no_words_for_keeps_its_values_as_read() -> None:
    """A colour controller's link: the library describes none of its modes."""
    link = {"mode": "M19 (Start/stop scenario)", "t1": "3", "t2": None}
    assert _explained("rgb_module", link) == {"mode": "M19 (Start/stop scenario)", "t1": "3"}


@pytest.mark.parametrize(
    "name",
    [
        meaning.HOLD_TIME,
        meaning.OFF_AFTER,
        meaning.ON_AFTER,
        meaning.RUN_TIME,
        meaning.LEVEL,
        meaning.DIM_TIME,
        meaning.DIM_ON_TIME,
        meaning.DIM_OFF_TIME,
    ],
)
def test_a_model_is_told_what_each_named_value_is(name: str) -> None:
    assert f"'{name}'" in API_PROMPT


@pytest.mark.parametrize(
    ("address", "record", "plate_number", "shown"),
    [
        pytest.param(PLATE, {"name": "Boudoir", "room": "Hall", "number": 11}, None, "11: Boudoir (Hall)", id="plate"),
        pytest.param(PLATE, {"name": "Boudoir", "room": "Hall"}, 7, "7: Boudoir (Hall)", id="number-from-the-pc-link"),
        pytest.param(PLATE, {"name": "Boudoir", "room": ""}, None, "Boudoir", id="no-room-no-number"),
        pytest.param(PLATE, {"name": "", "room": "Hall", "number": 3}, None, "3: Hall", id="unnamed-plate"),
        pytest.param(SWITCH, {"name": "Board", "room": "Cellar", "number": 2}, None, "Board (Cellar)", id="module"),
        pytest.param(PLATE, {"name": "", "room": ""}, 4, None, id="nothing-to-show"),
    ],
)
async def test_a_device_is_named_as_the_nikobus_integration_names_it(
    hass: HomeAssistant, setup: SetupFixture, address: str, record: dict[str, Any], plate_number: int | None, shown: str | None
) -> None:
    inventory = (await setup()).inventory
    inventory.names["devices"][address] = record
    inventory.buttons["nikobus_button"][PLATE]["component_number"] = plate_number
    assert inventory.device_name(address) == shown


async def test_the_gateway_is_the_nikobus_bridge(hass: HomeAssistant, setup: SetupFixture, entry: MockConfigEntry) -> None:
    await setup()
    gateway = dr.async_get(hass).async_get_device_by_identifier((DOMAIN, entry.entry_id), entry.entry_id)
    assert gateway is not None
    assert gateway.name == "Nikobus Bridge"


async def test_a_scene_has_a_device_of_its_own_that_stays(
    hass: HomeAssistant, hass_storage: dict[str, Any], scanned: SetupFixture, entry: MockConfigEntry
) -> None:
    """Named by the project, found by the real scan; a reload runs the clean-up of lost devices."""
    hass_storage[f"{DOMAIN}.{ENTRY_ID}"]["data"]["names"] = {
        "scenes": [{"name": "Dinner", "members": [[SWITCH, 5, "M14"], [SWITCH, 9, "M14"]]}]
    }
    hub = await scanned()
    devices = dr.async_get(hass)
    device = devices.async_get_device_by_identifier((DOMAIN, f"{KEY_SCENE}_scene"), entry.entry_id)
    assert device is not None
    assert (device.name, device.via_device_id) == ("Dinner", hub.group_device_id("scenes"))
    await hass.config_entries.async_reload(entry.entry_id)
    await _reloaded(hass, entry, hub)
    assert devices.async_get_device_by_identifier((DOMAIN, f"{KEY_SCENE}_scene"), entry.entry_id) is not None
    # What a module holds is not forgotten by deleting its device.
    assert not await async_remove_config_entry_device(hass, entry, device)


async def test_an_output_is_described_in_the_area_of_its_device(
    hass: HomeAssistant, setup: SetupFixture, entry: MockConfigEntry
) -> None:
    """The area is the module's: the entity has none of its own."""
    await setup()
    devices = dr.async_get(hass)
    module = devices.async_get_device_by_identifier((DOMAIN, SWITCH), entry.entry_id)
    assert module is not None
    devices.async_update_device(module.id, area_id=ar.async_get(hass).async_get_or_create("Cellar").id)
    described = await hass.services.async_call(DOMAIN, "describe", {}, blocking=True, return_response=True)
    assert {o["area"] for o in described["outputs"] if o["module"] == SWITCH and o["enabled"]} == {"Cellar"}


async def test_entities_are_labelled_by_kind_when_asked(
    hass: HomeAssistant, hass_storage: dict[str, Any], scanned: SetupFixture, entry: MockConfigEntry
) -> None:
    """The labels of the Nikobus integration, under its names; one already there is used, not doubled."""
    hass_storage[f"{DOMAIN}.{ENTRY_ID}"]["data"]["names"] = {
        "scenes": [{"name": "Dinner", "members": [[SWITCH, 5, "M14"], [SWITCH, 9, "M14"]]}]
    }
    labels = lr.async_get(hass)
    existing = labels.async_create("Nikobus Button")
    hub = await scanned()
    registry = er.async_get(hass)
    assert not registry.async_get(KEY_EVENT).labels
    result = await _options(hass, entry, {"next_step_id": "outputs"}, {"labels": True})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await _reloaded(hass, entry, hub)
    by_name = {label.name: label.label_id for label in labels.async_list_labels()}
    assert sorted(by_name) == ["Nikobus Button", "Nikobus Output", "Nikobus Scene"]
    assert registry.async_get(KEY_EVENT).labels == {existing.label_id}
    assert registry.async_get("switch.switch_module_4707_output_1").labels == {by_name["Nikobus Output"]}
    scene = registry.async_get_entity_id("scene", DOMAIN, f"{KEY_SCENE}_scene")
    assert registry.async_get(scene).labels == {by_name["Nikobus Scene"]}
    # The gateway's own entities are none of the three kinds.
    assert not registry.async_get("sensor.nikobus_bridge_discovery").labels


@pytest.mark.parametrize(
    ("named", "name", "entity_id"),
    [
        pytest.param(
            [{"name": "Dinner", "members": [[SWITCH, 5, "M14"], [SWITCH, 9, "M14"]]}], "Dinner", "scene.dinner", id="named-by-the-project"
        ),
        pytest.param([], None, None, id="a-key-and-nothing-more"),
    ],
)
async def test_an_output_names_the_scenes_it_is_part_of(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    scanned: SetupFixture,
    named: list[dict[str, Any]],
    name: str | None,
    entity_id: str | None,
) -> None:
    hass_storage[f"{DOMAIN}.{ENTRY_ID}"]["data"]["names"] = {"scenes": named}
    await scanned()
    described = await hass.services.async_call(DOMAIN, "describe", {}, blocking=True, return_response=True)
    output = next(o for o in described["outputs"] if (o["module"], o["channel"]) == (SWITCH, 5))
    assert output["scenes"] == [{"address": KEY_SCENE, "name": name, "entity_id": entity_id}]


async def test_an_entity_shows_what_it_is_on_the_bus(
    hass: HomeAssistant, hass_storage: dict[str, Any], scanned: SetupFixture
) -> None:
    """The details the Nikobus integration shows on its entities, from the links the scan read."""
    hass_storage[f"{DOMAIN}.{ENTRY_ID}"]["data"]["names"] = {
        "scenes": [{"name": "Dinner", "members": [[SWITCH, 5, "M14"], [SWITCH, 9, "M14"]]}]
    }
    await scanned()
    relay = hass.states.get("switch.switch_module_4707_output_1").attributes
    assert (relay["nikobus_address"], relay["channel"], relay["module_description"], relay["module_model"]) == (
        SWITCH,
        1,
        "Switch module",
        "05-000-02",
    )
    shutter = hass.states.get("cover.roller_shutter_module_9105_output_1").attributes
    # The run time of the link, 30 s, for both ways; the margin is the default.
    assert (shutter["operation_time_up"], shutter["operation_time_down"], shutter["end_stop_margin"]) == (30, 30, 3.0)
    assert (shutter["nikobus_address"], shutter["movement_source"]) == (ROLLER, None)
    key = hass.states.get(KEY_EVENT).attributes
    assert (key["wall_button_address"], key["wall_button_key"], key["wall_button_model"]) == (PLATE, "1C", "05-064")
    (linked,) = key["linked_outputs"]
    assert {k: linked[k] for k in ("module", "module_address", "channel", "mode", "t1", "t2", "does")} == {
        "module": "Switch module (4707)",
        "module_address": SWITCH,
        "channel": 1,
        "mode": "M05 (Impulse)",
        "t1": None,
        "t2": None,
        "does": "Each press switches the output over, on or off.",
    }
    # A shutter's link, with the value as read and as what it is.
    # Both keys of the pair drive it; the first is 1C.
    driver = shutter["controlled_by"][0]
    assert (driver["key"], driver["mode"], driver["t1"], driver["run_time"]) == (
        "1C",
        "M01 (Open - stop - close)",
        "30 s",
        "30 s",
    )
    scene = hass.states.get("scene.dinner").attributes
    assert (scene["bus_address"], scene["member_count"]) == (KEY_SCENE, 2)
    assert scene["triggered_by"] == [f"Bus push button, 4 control buttons #N037234 1C ({KEY_SCENE})"]
    assert [(o["module"], o["channel"], o["mode"]) for o in scene["outputs"]] == [
        ("Switch module (4707)", 5, "M14 (Light scene on)"),
        ("Switch module (4707)", 9, "M14 (Light scene on)"),
    ]
