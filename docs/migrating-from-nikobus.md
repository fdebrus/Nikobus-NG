# Moving from Nikobus to Nikobus NG

This guide takes an installation that runs the
[Nikobus integration](https://github.com/fdebrus/Nikobus-HA) to Nikobus NG,
keeping entity IDs, names, areas, dashboards, history and voice-assistant
exposure. It can be undone at every step until the last one.

It was followed on one real installation (a serial PC-Link, six output
modules, a Feedback Module, 44 plates; Home Assistant 2026.11). What that run
showed is noted where it matters.

> Nikobus NG is experimental. Nikobus stays, and stays maintained. Move if you
> want to try the new design, not because you have to.

## Why a second integration

Nikobus grew over years, one installation's report at a time. It works and
it is maintained, but its structure carries that history. A
[review of it](https://github.com/fdebrus/Nikobus-HA/blob/main/documentation/nikobus-ng-review.md)
listed what a fresh start could do differently; Nikobus NG is that fresh
start, on the same protocol library.

What it changes:

- **Entities hold no copy of the state.** An output shows what the module
  last reported, with pending commands laid on top by the library. The
  optimistic copies Nikobus keeps per entity were behind two regressions
  (a light changing state three times per switch, fixed in 3.30.3 for
  relays and in 3.31.4 for dimmers).
- **Keys are `event` entities**, Home Assistant's own way to show a button
  press, with one bus event instead of up to seven.
- **A shutter's movement is timed by Home Assistant's interval timer**, one
  tick per second while it moves, with the position calculation in the
  library. Nikobus runs background tasks of its own for it. The cover
  platform is 379 lines against 1,058.
- **Discovery is one step**, started by itself at first setup, instead of two
  buttons pressed in order.
- **Every output gets an entity**, named or not; one no key drives is created
  disabled.
- **The wiring is available as data**: which key drives which output, in
  which mode, for how long, in each entity's details, in the
  `nikobus_ng.describe` action and as tools for an AI assistant.
- **Tests run against the real Home Assistant core** and a simulated PC-Link.
  Nikobus is tested against a stub of Home Assistant, which cannot notice
  when the core changes.

In numbers, Nikobus 3.31.6 against Nikobus NG 0.10.3, integration code only:

| | Nikobus | Nikobus NG |
|---|---|---|
| Lines of Python | 15,037 | 6,009 |
| of which code (no comments, docstrings, blank lines) | 9,648 | 4,468 |
| Functions | 561 | 361 |
| Longest file | 2,066 lines | 722 lines |
| Longest function | 512 lines | 72 lines |
| Functions over 50 lines | 52 | 9 |

## In short

1. Back up Home Assistant and note what uses Nikobus events and actions.
2. Install Nikobus NG, disable the Nikobus entry, add Nikobus NG.
3. Let the discovery finish, then upload your `.nkb`.
4. Run **Take over from the Nikobus integration**.
5. Change by hand the automations that use Nikobus events or actions.
6. Live with it for a while. Keep the Nikobus entry disabled, not deleted.

Count an hour for a house of fifty outputs, most of it in step 5.

## Before you start

- **Home Assistant 2026.10 or later.**
- **A full backup** of Home Assistant. The take-over changes entity IDs; a
  backup is the one way back that does not depend on this integration.
- **Your `.nkb` project file** at hand, if you have one.
- **A list of what you will change by hand.** Search your automations,
  scripts and dashboards for:
  - `nikobus_button` and `nikobus_short_button`, `nikobus_long_button`: the
    Nikobus bus events;
  - `nikobus.`: the Nikobus actions;
  - the IDs of key entities you use (`binary_sensor.…`): a key is another kind
    of entity in Nikobus NG.

  In *Settings → Automations*, the search box finds the first two.

What you do **not** need to prepare: lights, switches, covers, fans, scenes
and input switches. The take-over carries them.

## Step 1: install Nikobus NG

In HACS, open the menu, choose *Custom repositories*, add
`https://github.com/fdebrus/Nikobus_NG` as an *Integration*, install
*Nikobus NG* and restart Home Assistant.

Installing changes nothing yet: the two integrations have different domains
(`nikobus` and `nikobus_ng`) and different stores.

## Step 2: hand the bus over

Only one program may talk to the bus.

1. *Settings → Devices & services → Nikobus → ⋮ → Disable.* **Disable, do not
   delete**: the take-over reads the Nikobus entities, and deleting the entry
   deletes them.
2. *Add integration → Nikobus NG*, and enter the same serial port or
   `host:port`.
3. Tick **A Feedback Module is installed** if you had it ticked in Nikobus.

A discovery starts by itself. Follow it on the *Discovery* sensor of the
**Nikobus Bridge** device; entities appear when it ends. On the installation
above it took a few minutes.

From here until step 4, your dashboards show the Nikobus entities as
unavailable. That is expected.

## Step 3: names

*Configure → Names from the project file*, upload the `.nkb`, leave *rooms as
areas* ticked.

Modules and plates take their names and rooms; a plate is shown as
`11: Boudoir (Hall)`, as in Nikobus.

Check before going on: open a few lights and a shutter under the Nikobus
Bridge and switch them. If something is wrong here, re-enable the Nikobus
entry and disable Nikobus NG: nothing of yours has been touched yet.

## Step 4: take over

*Configure → Take over from the Nikobus integration.* The form says how many
entities would move before anything does. Submit it; the entry reloads.

What moves onto Nikobus NG's entities:

| From Nikobus | What happens |
|---|---|
| Lights, switches, covers, fans, scenes, input switches | entity ID, name, area, aliases, labels, icon, voice-assistant exposure |
| A relay that was a light | becomes a light here too |
| Key press buttons | the same, and enabled where they were in use |
| Key sensors (`binary_sensor.…`) | the event entity takes the ID under `event.`, with name, area and labels; the sensor keeps its own ID |
| LED keys, shutter run times, end margins | added to the options, where none is set here |

The Nikobus entities are kept, parked under their ID followed by `_nikobus`.

After the reload, dashboards, history, HomeKit and voice assistants work
again without changes: they know the entities by their IDs, and the IDs are
the same.

If the menu still offers the take-over afterwards, something was left; run it
again. It leaves alone what it took before.

## Step 5: what you change by hand

### Automations on bus events

Nikobus fires one bus event per situation. Nikobus NG fires one event,
`nikobus_ng_press`, with a `type`.

| Nikobus event | In `nikobus_ng_press` |
|---|---|
| `nikobus_button_pressed` | `type: pressed` |
| `nikobus_button_timer_1`, `_2`, `_3` | `type: hold`, `seconds: 1`, `2`, `3` |
| `nikobus_short_button_pressed` | `type: short_release` |
| `nikobus_long_button_pressed` | `type: long_release` |
| `nikobus_button_released` | either release; `duration` is its `duration_s` |
| `nikobus_button_pressed_0` … `_3` | a release with `seconds: 0` … `3` |

Before:

```yaml
triggers:
  - trigger: event
    event_type: nikobus_button_pressed
    event_data:
      address: "9A93EE"
```

After:

```yaml
triggers:
  - trigger: event
    event_type: nikobus_ng_press
    event_data:
      address: "9A93EE"
      type: pressed
```

Do not leave `type` out: the automation would then fire on the press, on each
second it is held, and on the release.

A hold of two seconds, before and after:

```yaml
    event_type: nikobus_button_timer_2
    event_data:
      address: "2A2481"
```

```yaml
    event_type: nikobus_ng_press
    event_data:
      address: "2A2481"
      type: hold
      seconds: 2
```

Quote the address: an all-digit address with an `E` in it is otherwise read
as a number.

The new event carries `address`, `type`, and `seconds` or `duration` where
they apply. `duration_s` is `duration` and `bucket` is `seconds`;
`module_address`, `channel`, `press_id`, `ts`, `state`, `threshold_s` and
`source` have no counterpart.

### Automations that read a key's sensor

A key was a binary sensor with the states `pressed` and `idle`. It is an
event entity now, whose state is the time of its last event. Trigger on the
event entity, or on the bus event above:

```yaml
triggers:
  - trigger: state
    entity_id: event.bt_hall_ceiling_up
conditions:
  - condition: state
    entity_id: event.bt_hall_ceiling_up
    attribute: event_type
    state: pressed
```

After the take-over the event entity has the sensor's name under `event.`:
`binary_sensor.bt_hall_ceiling_up` gives `event.bt_hall_ceiling_up`.

### Actions

| Nikobus | Nikobus NG |
|---|---|
| `nikobus.send_button_press` (`address`) | `nikobus_ng.press_key` (`address`) |
| `nikobus.refresh_module` (`address`, `group`) | `nikobus_ng.read_module` (`address`); it reads both groups |
| `nikobus.query_module_inventory` | `nikobus_ng.discover` (`address` for one module) |
| `nikobus.verify_modules` (`addresses`) | `nikobus_ng.verify_programming` (`modules`) |
| `nikobus.backup_modules` (`addresses`) | `nikobus_ng.backup_programming` (`modules`) |
| `nikobus.sync_pc_link_clock` | the *Set PC-Link clock* button of the Nikobus Bridge |
| `nikobus.detect_stale_inventory`, `purge_stale_inventory` | none: delete the device, or use the repair of a module that stopped answering |

### The bridge's own entities

They are not taken over; Nikobus NG has its own, under other IDs. A
dashboard that shows them needs the new ones.

| Nikobus | Nikobus NG |
|---|---|
| Connection (sensor) | Connection (binary sensor) |
| Discovery status, Discovery progress | Discovery, with `progress` as an attribute |
| PC-Link clock | PC-Link clock, with `seconds_ahead` as an attribute |
| Programming health | Programming |
| The three numbered discovery buttons | one button, *Discover installation* |

Where the Nikobus sensor still holds the ID, the new one gets a suffix:
`sensor.nikobus_bridge_pc_link_clock_2`.

### Attributes

Templates that read entity attributes mostly keep working: outputs keep
`nikobus_address`, `channel`, `module_description`, `module_model` and
`controlled_by`; shutters keep `operation_time_up`, `operation_time_down` and
`end_stop_margin`; keys keep `wall_button_address`, `wall_button_key` and
`linked_outputs`. Each link carries `mode`, `t1` and `t2` as before, plus a
sentence, `does`, on what it does.

## What will look different

- **Names, from Home Assistant 2026.11.** Home Assistant now shows the
  device's name in front of an entity's. A light reads "Dimcontroller
  (Cellar) Wall lights" where the Nikobus entity, named before that upgrade,
  read "Wall lights". Aliases and voice exposure are carried, so an assistant
  still knows the short name.
- **Devices are filed by kind** under the bridge: *Output modules*, *System
  modules*, *Wall buttons*, *Remotes*, *Interfaces*, *Scenes*, *Shutter groups*.
- **One device per plate**, with an event entity and a press button per key,
  instead of one device per key.
- **Logical inputs** are named by their address ("PC-Logic Logical Input
  #N64A061"), not "LM-INPUT 1"; their switches keep the IDs they had.
- **An output no key drives** is created disabled. The take-over enables the
  ones you used in Nikobus.

## What Nikobus NG does not have

| In Nikobus | Here |
|---|---|
| Scenes made in the options | use Home Assistant's own scenes |
| Choosing which kinds of key get entities | all get one; disable what you do not want |
| A refresh interval to set | fixed: two minutes, or five behind a Feedback Module |
| A device per PC-Link calendar channel | named in `controlled_by` only |

## Going back

Until you delete the Nikobus entry, the way back is:

1. *Configure → Give back to the Nikobus integration.* Each Nikobus entity
   gets its ID back; Nikobus NG's entities return to the IDs they had.
2. Disable the Nikobus NG entry.
3. Enable the Nikobus entry.
4. Put back the automations you changed in step 5.

Names, areas and aliases stay as they are on both sides.

## When you are sure

Keep the Nikobus entry **disabled** for as long as you might want to go back.
Deleting it deletes the parked entities, and with them the *Give back* step.

When you no longer need that:

1. Delete the Nikobus entry.
2. Remove the Nikobus integration in HACS.
3. Restart Home Assistant.

Nikobus NG then keeps running as it is; it does not depend on the Nikobus
integration being installed.

## If something goes wrong

| What you see | What to do |
|---|---|
| The take-over is refused: "the Nikobus integration is running" | Disable the Nikobus entry first. |
| No *Take over* in the menu | Nothing is left to take, or the discovery has not finished. |
| A repair "module is not answering" for a module you do not have | A PC-Link keeps listing what was once in its project. Delete that device; it stays out. |
| A shutter or an output is missing | It is created disabled when no key drives it. Enable the entity. |
| A shutter's position drifts on closing | Only the times set in Nikobus are carried. Set the closing time under *Configure → A roller output*. |
| Entities stay unavailable after the take-over | Check the *Connection* sensor of the Nikobus Bridge; make sure no other program holds the port. |
| An automation fires several times per press | It triggers on `nikobus_ng_press` without `type`. |

For anything else, open an
[issue](https://github.com/fdebrus/Nikobus_NG/issues) with the integration's
*Download diagnostics* file; it holds addresses and counts, no names.

## What has and has not been seen

Seen on the one real installation: the discovery, the names from the `.nkb`,
a take-over of 45 outputs, 3 scenes, 6 input switches and 152 keys with their
press buttons, the import of shutter run times, and the three automations
above converted and saved.

Not yet seen there: a key pressed or held at the wall arriving as an event in
Nikobus NG, the import of LED keys (that installation had none), and *Give
back* on a real registry.
