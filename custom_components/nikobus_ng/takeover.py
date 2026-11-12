"""Taking over the entities of the Nikobus integration, and giving them back.

Both integrations describe the same outputs. Dashboards, automations
and voice assistants know them by the entity ids, names, areas and
aliases they have under the Nikobus integration. A take-over moves
those onto this integration's entities: the Nikobus entity is parked
under another id, and this integration's entity takes its id, the name
it is shown under, its area, aliases, labels, icon and what it is
exposed to.
History follows, since it is kept by entity id.

An entity id belongs to one entity, so this is a change of hands, not a
copy. It is recorded, and giving back undoes it.

A key is a binary sensor there and an event entity here, so its entity
id cannot change hands. The event entity takes the sensor's id under
``event.``, with its name, area, aliases and labels, and the sensor
keeps its own id. A key's press button is a button on both sides and
changes hands like an output.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.util.json import load_json

from .const import (
    CONF_FAN_OUTPUTS,
    CONF_LED_KEYS,
    CONF_LIGHT_OUTPUTS,
    CONF_SHUTTERS,
    CONF_USE_AS,
    DIMMER_MODULE,
    DOMAIN,
    ROLLER_MODULE,
    SWITCH_MODULE,
)
from .manual import led_keys_of, run_times_of

if TYPE_CHECKING:
    from .hub import NikobusHub

_LOGGER = logging.getLogger(__name__)

OLD_DOMAIN = "nikobus"
#: Where the Nikobus integration keeps its modules, with what is set per output.
OLD_MODULE_STORE = "nikobus.modules"
_KEY = re.compile(r"^[0-9A-F]{6}$")
#: What a parked Nikobus entity's id ends in.
PARKED = "_nikobus"

# The unique ids the Nikobus integration gives: an output, a shutter
# group, a central function, a logical input's switch, a key's sensor
# and its press button.
_OUTPUT = re.compile(r"^nikobus_(light|switch|cover|fan)_[a-z_]+_([0-9A-Fa-f]{4})_(\d+)$")
_OTHERS = (
    (re.compile(r"^nikobus_cf_cover_([0-9A-Fa-f]{6})$"), "cover", "{}_group"),
    (re.compile(r"^nikobus_cf_([0-9A-Fa-f]{6})$"), "scene", "{}_scene"),
    (re.compile(r"^nikobus_input_switch_([0-9A-Fa-f]{6})$"), "switch", "{}_input"),
    (re.compile(r"^nikobus_button_([0-9A-Fa-f]{6})$"), "event", "{}_event"),
    (re.compile(r"^nikobus_push_button_([0-9A-Fa-f]{6})$"), "button", "{}_press"),
)


@dataclass(slots=True)
class Plan:
    """What a take-over would do."""

    #: ``{"entity_id", "domain", "unique_id", "name"}`` per entity to take over.
    entities: list[dict[str, str]] = field(default_factory=list)
    #: The options that make this integration's outputs the same kind of entity.
    options: dict[str, Any] = field(default_factory=dict)
    #: Nikobus entities with no counterpart here: its bridge's own, and what the inventory lacks.
    left: int = 0


@dataclass(slots=True)
class Settings:
    """What the Nikobus integration holds per output and this integration does not."""

    #: ``{"<module>:<channel>": {"on_key", "off_key"}}`` to add to the LED keys.
    led_keys: dict[str, dict[str, str]] = field(default_factory=dict)
    #: ``{"<module>:<channel>": {"open_time", "close_time", "end_margin"}}`` to add to the shutters.
    shutters: dict[str, dict[str, float]] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.led_keys or self.shutters)


async def async_nikobus_settings(hass: HomeAssistant, hub: NikobusHub) -> Settings:
    """The LED keys and shutter run times set in the Nikobus integration, where none is set here.

    They are in its module store, per output, not in any registry. The
    store is read as the file it is, and never written. What is already
    set here is left as it is.
    """
    try:
        stored = await hass.async_add_executor_job(load_json, hass.config.path(STORAGE_DIR, OLD_MODULE_STORE))
    except HomeAssistantError:
        # Not a file that can be read: there is nothing to take from it.
        return Settings()
    data = stored.get("data") if isinstance(stored, dict) else None
    modules = data.get("nikobus_module") if isinstance(data, dict) else None
    settings = Settings()
    if not isinstance(modules, dict):
        return settings
    for module in hub.inventory.output_modules():
        entry = modules.get(module.address) or modules.get(module.address.lower())
        channels = entry.get("channels") if isinstance(entry, dict) else None
        if not isinstance(channels, list):
            continue
        for number, channel in enumerate(channels[: module.channels], start=1):
            if not isinstance(channel, dict):
                continue
            output = f"{module.address}:{number}"
            led = {
                option: key
                for option, key in led_keys_of(channel).items()
                if _KEY.match(key)
            }
            if led and output not in hub.led_keys:
                settings.led_keys[output] = led
            if module.module_type != ROLLER_MODULE:
                continue
            mine = hub.shutters.get(output, {})
            if times := {option: value for option, value in run_times_of(channel).items() if option not in mine}:
                settings.shutters[output] = times
    return settings


def merged_options(plan: Plan, settings: Settings, hub: NikobusHub) -> dict[str, Any]:
    """The options a take-over saves: the plan's, with the Nikobus integration's settings filled in."""
    shutters = {output: dict(values) for output, values in plan.options[CONF_SHUTTERS].items()}
    for output, times in settings.shutters.items():
        shutters[output] = {**times, **shutters.get(output, {})}
    return {
        **plan.options,
        CONF_SHUTTERS: shutters,
        CONF_LED_KEYS: {**settings.led_keys, **hub.led_keys},
    }


def old_entry_blocks(hass: HomeAssistant) -> bool:
    """Whether the Nikobus integration is running: its entities are then in use."""
    return any(
        entry.state is ConfigEntryState.LOADED for entry in hass.config_entries.async_entries(OLD_DOMAIN)
    )


def has_old_entities(hass: HomeAssistant) -> bool:
    """Whether the Nikobus integration left entities to take over."""
    return any(entry.platform == OLD_DOMAIN for entry in er.async_get(hass).entities.values())


def _shown_name(hass: HomeAssistant, entry: er.RegistryEntry) -> str:
    """The name the Nikobus entity is shown under, as Home Assistant composes it."""
    return er.async_get_legacy_friendly_name(hass, entry)


def _carried_name(old: er.RegistryEntry, mine: er.RegistryEntry | None, shown: str) -> str | None:
    """The name to give this integration's entity so that it reads as the Nikobus one did.

    Up to Home Assistant 2026.10 a name set in the registry is shown as
    it is, so the whole shown name is carried. From 2026.11 the device's
    name is always put in front of it, so only the entity's own part is
    carried: the name a person gave it, else the one the Nikobus
    integration gave it; nothing where that is this entity's name already.
    """
    if not hasattr(old, "compat_name"):
        return shown or None
    part = old.name or old.original_name
    return part if part and mine is not None and part != mine.original_name else None


def _used(old: er.RegistryEntry) -> bool:
    """Whether the Nikobus entity was in use: enabled, or disabled only because its entry is."""
    return old.disabled_by in (None, er.RegistryEntryDisabler.CONFIG_ENTRY)


def make_plan(hass: HomeAssistant, hub: NikobusHub) -> Plan:
    """Match every Nikobus entity to this integration's, and say what would change."""
    inventory = hub.inventory
    modules = {module.address: module for module in inventory.output_modules()}
    colour = {address for address, _ in inventory.rgb_modules()}
    lights = set(hub.light_outputs)
    fans = set(hub.fan_outputs)
    shutters = {output: dict(settings) for output, settings in hub.shutters.items()}
    plan = Plan()
    taken = {(item["domain"], item["unique_id"]) for item in inventory.takeover["done"]}
    for entry in sorted(er.async_get(hass).entities.values(), key=lambda e: e.entity_id):
        if entry.platform != OLD_DOMAIN:
            continue
        target: tuple[str, str] | None = None
        if match := _OUTPUT.match(entry.unique_id):
            address, channel = match[2].upper(), int(match[3])
            output = f"{address}:{channel}"
            if address in colour:
                target = ("light", f"{address}_rgb")
            elif (module := modules.get(address)) and channel <= module.channels:
                target = (entry.domain, f"{address}_{channel}")
                # The same kind of entity here as there.
                if module.module_type == SWITCH_MODULE:
                    (lights.add if entry.domain == "light" else lights.discard)(output)
                elif module.module_type == DIMMER_MODULE:
                    (fans.add if entry.domain == "fan" else fans.discard)(output)
                elif module.module_type == ROLLER_MODULE:
                    settings = shutters.setdefault(output, {})
                    settings.pop(CONF_USE_AS, None)
                    if entry.domain in ("light", "switch"):
                        settings[CONF_USE_AS] = entry.domain
                    if not settings:
                        del shutters[output]
        else:
            for pattern, domain, unique_id in _OTHERS:
                if match := pattern.match(entry.unique_id):
                    target = (domain, unique_id.format(match[1].upper()))
                    break
        if target is None:
            plan.left += 1
            continue
        if target in taken:
            # Taken over before: its Nikobus entity is parked, and not to be taken again.
            continue
        plan.entities.append(
            {
                "entity_id": entry.entity_id,
                "domain": target[0],
                "unique_id": target[1],
                "name": _shown_name(hass, entry),
            }
        )
    plan.options = {
        CONF_LIGHT_OUTPUTS: sorted(lights),
        CONF_FAN_OUTPUTS: sorted(fans),
        CONF_SHUTTERS: shutters,
    }
    return plan


def apply_pending(hass: HomeAssistant, hub: NikobusHub) -> int:
    """Move the ids and what goes with them. Run once the entities exist; returns how many moved."""
    inventory = hub.inventory
    registry = er.async_get(hass)
    devices = dr.async_get(hass)
    pending, inventory.takeover["pending"] = inventory.takeover["pending"], []
    for item in pending:
        old = registry.async_get(item["entity_id"])
        mine_id = registry.async_get_entity_id(item["domain"], DOMAIN, item["unique_id"])
        if old is None or old.platform != OLD_DOMAIN or mine_id is None:
            _LOGGER.warning("%s was not taken over: it has no counterpart here", item["entity_id"])
            continue
        # Another kind of entity here: the id's name is taken, and the Nikobus entity keeps its id.
        same_kind = old.domain == item["domain"]
        taken = item["entity_id"] if same_kind else f"{item['domain']}.{old.entity_id.partition('.')[2]}"
        parked = f"{item['entity_id']}{PARKED}" if same_kind else None
        in_the_way = parked if parked else (taken if taken != mine_id else None)
        if in_the_way and registry.async_get(in_the_way):
            _LOGGER.warning("%s was not taken over: %s is in use", item["entity_id"], in_the_way)
            continue
        mine = registry.async_get(mine_id)
        device = devices.async_get(old.device_id) if old.device_id else None
        if parked:
            registry.async_update_entity(old.entity_id, new_entity_id=parked)
        changes: dict[str, Any] = {
            "name": _carried_name(old, mine, item["name"]),
            "area_id": old.area_id or (device.area_id if device else None),
            "aliases": old.aliases,
            "labels": old.labels,
            "icon": old.icon,
            "hidden_by": old.hidden_by,
        }
        if taken != mine_id:
            changes["new_entity_id"] = taken
        if _used(old) and mine and mine.disabled_by is er.RegistryEntryDisabler.INTEGRATION:
            # Used there, so wanted here, whatever the links say.
            changes["disabled_by"] = None
        registry.async_update_entity(mine_id, **changes)
        for domain, options in old.options.items():
            registry.async_update_entity_options(taken, domain, dict(options))
        inventory.takeover["done"].append(
            {**item, "taken_entity_id": taken, "previous_entity_id": mine_id, "parked": parked}
        )
    return len(inventory.takeover["done"])


def repair_taken(hass: HomeAssistant, hub: NikobusHub) -> int:
    """Put right what an earlier take-over left wrong; returns how many entities changed.

    Up to 0.8.0 the whole shown name was carried on every Home Assistant,
    which from 2026.11 reads with the device's name twice, and an entity
    whose Nikobus entry was disabled counted as unused and stayed
    disabled here. A name changed since by a person is left alone.
    """
    registry = er.async_get(hass)
    repaired = 0
    for item in hub.inventory.takeover["done"]:
        mine_id = registry.async_get_entity_id(item["domain"], DOMAIN, item["unique_id"])
        old = registry.async_get(item["parked"] or item["entity_id"])
        mine = registry.async_get(mine_id) if mine_id else None
        if mine is None or old is None or old.platform != OLD_DOMAIN:
            continue
        changes: dict[str, Any] = {}
        name = _carried_name(old, mine, item["name"])
        if mine.name == (item["name"] or None) and mine.name != name:
            changes["name"] = name
        if _used(old) and mine.disabled_by is er.RegistryEntryDisabler.INTEGRATION:
            changes["disabled_by"] = None
        if changes:
            registry.async_update_entity(mine.entity_id, **changes)
            repaired += 1
    return repaired


def give_back(hass: HomeAssistant, hub: NikobusHub) -> int:
    """Undo a take-over: each entity gets the id it had before. Returns how many were given back."""
    inventory = hub.inventory
    registry = er.async_get(hass)
    given = 0
    for item in reversed(inventory.takeover["done"]):
        taken = item.get("taken_entity_id", item["entity_id"])
        mine_id = registry.async_get_entity_id(item["domain"], DOMAIN, item["unique_id"])
        if mine_id == taken and taken != item["previous_entity_id"]:
            free = registry.async_get(item["previous_entity_id"]) is None
            registry.async_update_entity(
                mine_id, new_entity_id=item["previous_entity_id"] if free else f"{taken}_ng"
            )
        if item["parked"] is None:
            # A key: the Nikobus entity never left its id.
            given += 1
            continue
        parked = registry.async_get(item["parked"])
        if parked is not None and parked.platform == OLD_DOMAIN and registry.async_get(item["entity_id"]) is None:
            registry.async_update_entity(item["parked"], new_entity_id=item["entity_id"])
            given += 1
    inventory.takeover = {"pending": [], "done": []}
    return given
