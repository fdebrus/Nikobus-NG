# Nikobus NG for Home Assistant

<p align="left">
  <a href="https://www.buymeacoffee.com/fdebrus"><img src="https://img.shields.io/badge/Support-Buy%20Me%20a%20Coffee-FFDD00?style=flat&logo=buymeacoffee" alt="Buy Me a Coffee"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-Nikobus%20NG-blue?style=flat&logo=homeassistant" alt="Nikobus NG for Home Assistant">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange?style=flat" alt="HACS Custom"></a>
  <img src="https://img.shields.io/badge/Status-Experimental-red?style=flat" alt="Experimental">
  <a href="https://github.com/fdebrus/Nikobus_NG"><img src="https://img.shields.io/badge/Maintained%20by-fdebrus-green?style=flat" alt="Maintainer"></a>
  <a href="https://github.com/fdebrus/Nikobus_NG/releases"><img src="https://img.shields.io/github/v/release/fdebrus/Nikobus_NG?style=flat&label=Release" alt="Latest release"></a>
  <a href="https://github.com/fdebrus/Nikobus_NG/issues"><img src="https://img.shields.io/github/issues/fdebrus/Nikobus_NG?style=flat&label=Issues" alt="Open issues"></a>
  <a href="https://github.com/fdebrus/Nikobus_NG/stargazers"><img src="https://img.shields.io/github/stars/fdebrus/Nikobus_NG?style=flat&label=Stars" alt="GitHub stars"></a>
</p>

Control your **Nikobus** installation from Home Assistant: switches, dimmers and shutters as native entities, every key as an event for your automations, and the wiring of the installation as data an AI assistant can read. Modules, plates and links are **read from the bus in one discovery**, and names, rooms and scenes come from your **`.nkb` project file**.

Nikobus NG ("Next Generation") is a second integration, written from scratch next to the [Nikobus integration](https://github.com/fdebrus/Nikobus-HA) on the same protocol library, [nikobus-connect](https://github.com/fdebrus/nikobus-connect). The name says what it is: a fresh design of the same thing, not its successor yet. Nikobus stays, and stays maintained. The two use different domains and can be installed side by side, one enabled at a time.

> **Experimental.** Nikobus NG runs on one real installation so far, and most of it has only been tested against a simulated PC-Link. [What is verified](#what-is-verified) says exactly what has and has not been seen on hardware. Testers are welcome, especially with hardware listed there as not seen.

### Highlights

- 🔌 **One discovery** — one button reads the PC-Link inventory and every module's links, and it starts by itself on first setup. One module can be read again on its own.
- 💡 **Native entities** — a relay is a `switch` or a `light`, a dimmer output a `light` with brightness or a `fan` with speed, a shutter a `cover` with an estimated position.
- 🎛️ **Keys are event entities** — one per key, with `pressed`, `hold`, `short_release` and `long_release`, plus one bus event for automations on any address.
- 🤖 **Made for AI assistants** — an action and a set of tools return the wiring: which key drives which output, in which mode, said in plain words. An assistant can answer "which button switches the kitchen light?".
- 🧭 **Every output names what drives it** — the keys and PC-Link calendar channels are in its `controlled_by` attribute.
- 📥 **Names from your `.nkb`** — modules, plates (numbered as in the Nikobus software), outputs, rooms as areas, and light scenes.
- 🎬 **Scenes and shutter groups** — light scenes are activated by their own telegram; a function that only moves shutters is a `cover` for the group.
- 🚥 **LED keys** — an output can be switched by pressing its key, so the plate's LED follows what Home Assistant does.
- 🔊 **Audio zones and RGB controller** — a `media_player` per zone, a `light` for a colour controller.
- 🩺 **Repairs that say what to do** — a module that stopped answering or was reprogrammed, a wrong port, a module of the wrong type; several come with a fix button.
- 🛡️ **Read-only maintenance** — check every module's programming, back up its memory, see the PC-Link's clock. Setting that clock is the only thing ever written.
- 🔁 **A take-over from Nikobus** — moves entity IDs, names, areas, labels, voice exposure, LED keys and shutter run times across, and can be undone.

---

## Quick start

1. **Disable the Nikobus entry** if you have one: only one program may talk to the bus.
2. **Install** through HACS as a custom repository (button below) and restart Home Assistant.
3. **Add the integration**: *Settings → Devices & services → Add integration → Nikobus NG*. Enter the serial port (`/dev/ttyUSB0`) or the TCP bridge (`192.168.2.50:9999`).
4. **Wait for the discovery.** It starts by itself; follow it on the *Discovery* sensor of the **Nikobus Bridge** device. Entities appear when it ends. A large installation takes a few minutes.
5. *(Optional)* **Upload your `.nkb`** under *Configure → Import names (.nkb)* for names, rooms and scenes.
6. *(Optional)* Press **Back up programming** once and keep the folder somewhere safe.

Coming from the Nikobus integration? See [Coming from Nikobus](#coming-from-nikobus).

---

## Prerequisites

- **Home Assistant 2026.10 or later.**
- **A serial gateway to the bus**, normally a **PC-Link (05-200)**: it holds the inventory the discovery reads and relays everything on the bus. Without one, the `.nkb` project file or two hand-written files can stand in for the inventory.
- **One client at a time.** Stop the Nikobus PC software, and disable the Nikobus integration, before starting Nikobus NG.
- **A connection path**: a USB/serial adapter or a TCP-to-serial bridge (`host:port`).
- *(Optional)* **a Feedback Module (05-207)**. Tick the option at setup when Home Assistant is on the PC-Link's port: the module's own reads are then picked up and Home Assistant reads only what it leaves out.
- *(Optional)* **your `.nkb` project file**, the only place your names, rooms and scene names live.

---

## Installation & setup

1. Install through HACS with the button below, or add `https://github.com/fdebrus/Nikobus_NG` under *HACS → ⋮ → Custom repositories* as an *Integration*:

   [![Add to HACS](https://img.shields.io/badge/HACS-Add%20Custom%20Repository-blue.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=fdebrus&repository=Nikobus_NG&category=integration)

   Without HACS, copy `custom_components/nikobus_ng` into `config/custom_components`, under that exact name.
2. Restart Home Assistant.
3. *Settings → Devices & services → Add integration → Nikobus NG*, and enter the serial path or `host:port`. The connection is tested at once.
4. Tick **A Feedback Module is installed** if it applies.

Everything else is under **Configure** on the integration's entry:

| Menu | What it sets |
|---|---|
| Import names (.nkb) | upload the `.nkb`: names, rooms as areas, scene names |
| Lights and fans | which relays are lights, which dimmer outputs are fans, labels by kind |
| Shutter run times | show it as a cover, switch or light; its run times and end margin |
| Keep button LEDs in sync | the keys pressed to switch it on and off, so the plate's LED follows |
| Gateway | Feedback Module, a PC-Link older than generation 3, telegrams per press |
| Correct a module's type | correct a module the inventory has as another type |
| Import inventory files | for an installation with neither a PC-Link nor a `.nkb` |
| Take over from Nikobus | see [Coming from Nikobus](#coming-from-nikobus) |

To change the connection itself, use **Reconfigure** on the entry.

---

## What you get

| In your installation | In Home Assistant |
|---|---|
| Switch module output | `switch`, or `light` when ticked as switching a lamp |
| Dimmer output | `light` with brightness, or `fan` with speed |
| Roller output | `cover` with a position estimated from its run times |
| Light scene (central function) | `scene`, activated by its own telegram |
| Function that only moves shutters | `cover` for the group |
| Each key of a plate, remote or interface | `event` entity, and a press `button` (created disabled) |
| PC-Logic or Modular Interface input | `switch` that follows and sends its two frames |
| Motion detector | occupancy and light-level `binary_sensor` |
| Audio distribution zone | `media_player`: on, off, volume steps, source |
| RGB controller | `light`: on or off and its colour, switched by its linked keys |
| The gateway | connection, discovery, programming and clock sensors; four buttons |

Devices are filed by kind under the **Nikobus Bridge**: *Output modules*, *System modules*, *Wall buttons*, *Remotes*, *Interfaces*, *Scenes* and *Shutter groups*. A plate the project file names is shown as `11: Boudoir (Hall)`, a module as `Dimcontroller (Cellar)`.

Each entity shows what it is on the bus in its attributes, with every link as the module holds it (`mode`, `t1`, `t2`, the record itself) next to what it does: an output its module, channel and the keys that drive it; a shutter its run times and end margin; a key its plate and the outputs it drives, with what each link does; a scene its outputs and the keys that trigger it.

An output no key drives is created disabled; enable it if you use it from Home Assistant only. Deleting the device of a module or a plate leaves it out from then on, through later discoveries too.

---

## Key presses in automations

A press gives `pressed` at its first telegram, `hold` with `seconds` 1, 2 and 3 while it goes on, and at its end `short_release` (under a second) or `long_release`, with `duration` and with `seconds`, the whole seconds it was held (3 for three or more).

Trigger on the key's **event entity**, or on the bus event **`nikobus_ng_press`**, which also fires for an address the inventory does not know:

```yaml
triggers:
  - trigger: event
    event_type: nikobus_ng_press
    event_data:
      address: "9A93EE"
      type: hold
      seconds: 2
```

Quote the address: an all-digit address with an `E` in it is otherwise read as a number.

A blueprint, [`nikobus_ng_key_controls_entity.yaml`](blueprints/automation/fdebrus/nikobus_ng_key_controls_entity.yaml), lets a key switch an entity of any integration.

---

## For AI assistants

Home Assistant shows an entity and its state. It cannot show the wiring: which key drives which output, in which mode, for how long. Nikobus NG returns it as data.

- **The `nikobus_ng.describe` action** returns the whole installation: every output with the keys that drive it, every key with what it drives, the scenes with their outputs, the health of the bus.
- **An LLM API, "Nikobus NG"**, offers the same in pieces to Home Assistant's conversation agents and its MCP server: `nikobus_overview`, `nikobus_output`, `nikobus_key`, `nikobus_scenes`, `nikobus_health`, and `nikobus_press_key`. The first five only read.

A link is said in words, with its values under what they are instead of the vendor's T1 and T2:

```json
{
  "mode": "M12 (Preset on)",
  "does": "Sets the output to 40 % (4,0 V), whatever its last level. Dimming takes 4 s.",
  "level": "40 % (4,0 V)",
  "dim_time": "4 s"
}
```

The wording is the library's, taken from the vendor's manuals. A mode on two or four keys is said for the key the link is on: "This key switches the output on; the lower key of the pair switches it off." On a plate, keys A and C are the upper ones, B and D the lower ones.

---

## Coming from Nikobus

Nikobus NG can be tried without losing anything: it has its own domain and its own store, and re-enabling the Nikobus entry takes you back.

The step-by-step guide, with the actions and entities that change and the way back, is **[Moving from Nikobus to Nikobus NG](docs/migrating-from-nikobus.md)**.

**Take over** (*Configure → Take over from Nikobus*), with the Nikobus entry disabled, moves onto Nikobus NG's entities:

- the entity ID, name, area, aliases, labels, icon and voice-assistant exposure of lights, switches, covers, fans, scenes, input switches and key press buttons, so dashboards, automations and history keep working;
- relays that were lights become lights;
- the LED keys, shutter run times and end margins set per output.

The form says what it would do before anything moves. The Nikobus entities are parked under their ID followed by `_nikobus`, and **Give back** undoes it. It can be run again; what was taken before is left alone.

What you change by hand:

- **Automations on Nikobus bus events.** A key is a binary sensor in Nikobus and an event entity here; the event entity takes the sensor's ID under `event.`.

  | Nikobus bus event | Here: `type` of `nikobus_ng_press` |
  |---|---|
  | `nikobus_button_pressed` | `pressed` |
  | `nikobus_button_timer_1`, `_2`, `_3` | `hold` with `seconds` 1, 2, 3 |
  | `nikobus_short_button_pressed` | `short_release` |
  | `nikobus_long_button_pressed` | `long_release` |
  | `nikobus_button_released` | either release; `duration` is its `duration_s` |
  | `nikobus_button_pressed_0` … `_3` | a release with `seconds` 0 … 3 |

- **Names, from Home Assistant 2026.11.** Home Assistant now always shows the device's name in front of an entity's. An output reads "Dimcontroller (Cellar) Wall lights" where the Nikobus entity, named before that upgrade, still reads "Wall lights". Aliases and voice exposure are carried, so an assistant still knows the short name.

How the two differ:

| | Nikobus | Nikobus NG |
|---|---|---|
| Discovery | two buttons, in order | one action, automatic on first setup |
| Keys | binary sensors and up to seven kinds of bus event | `event` entities, one bus event |
| Relay as light, dimmer as fan | module customisation | two tick lists |
| Outputs without a name | no entity | an entity, disabled when no key drives it |
| Gone modules and plates | detect, then purge | a repair; or delete the device |
| Scenes made in the options | yes | no: use Home Assistant's own scenes |
| Refresh interval | adjustable | fixed |
| Tests | against a stub of Home Assistant | against the real core and a simulated bus |

---

## Supported hardware

What the PC-Link inventory and the link scan recognise comes from the library and is the same as for the [Nikobus integration](https://github.com/fdebrus/Nikobus-HA#supported-hardware). The last column says what Nikobus NG itself has met on a real installation.

| Hardware | Ref | Seen on real hardware |
|---|---|---|
| Switch module, compact switch module | `05-000-02`, `05-002-02` | yes |
| Dim controller | `05-007-02` | yes |
| Compact dim controller | `05-008-02` | no |
| Roller shutter module | `05-001-02` | yes |
| PC-Link | `05-200` | yes, generation 3 or later |
| PC-Logic, its logical inputs | `05-201` | yes |
| Feedback Module | `05-207` | yes, its reads picked up; LED keys not yet |
| Modular Interface | `05-206` | no |
| Audio distribution module | `05-205` | no |
| RGB controller | `340-00112` | no |
| Bus push buttons, 2, 4 and 8 keys | `05-060`, `05-064`, `4*-078` | yes |
| Push button with IR receiver | `05-09x` | yes |
| Push buttons with feedback LEDs | `05-061`, `05-060-02`, `05-064-02`, `05-078-02` | no |
| RF-bus push buttons, mini RF transmitter | `05-302`, `05-304`, `05-311` | yes |
| Universal interface | `05-058` | yes |
| Motion detector | `05-7*5` | no |
| No PC-Link: `.nkb` or two files as inventory | | no |

"Yes" means discovered, its links read and its state shown.

---

## What is verified

Nikobus NG is tested against the real Home Assistant and `nikobus-simulator`, the simulated PC-Link shipped with the library. Nothing of Home Assistant or of the library is replaced in the tests.

**Seen on the one real installation** (a serial PC-Link, six output modules, a Feedback Module, 44 plates; Home Assistant 2026.11):

- Setup, both passes of the discovery, and the read of every output group.
- Names, rooms and the three light scenes from its `.nkb`; six logical inputs.
- A light scene activated from Home Assistant: its key went on the bus and the dimmer it holds went to its preset (4,0 V in the link, `0x66` of `0xFF` read back).
- The PC-Link's clock read, and set: from 47 minutes ahead to one second.
- The description: 52 outputs, 154 keys, 4 scenes, 6 logical inputs.
- A module the PC-Link lists but that is not on the bus: reported, and kept out once its device was deleted.
- A take-over of 45 outputs, 3 scenes, 6 input switches and 152 keys with their press buttons.
- Devices filed by kind under the bridge.

**Not yet seen on real hardware:**

- A key pressed or held at the wall, as events in Nikobus NG.
- Switching an output and moving a shutter from Home Assistant, observed end to end.
- LED keys with a Feedback Module.
- An audio module, an RGB controller, a motion detector, a Modular Interface.
- An installation without a PC-Link, and a PC-Link older than generation 3.
- A module's checksum check and memory backup.
- The AI tools used by a real conversation agent.
- The take-over's import of LED keys and shutter run times from a real Nikobus store.

**Limits of the tests themselves:**

- The simulator has no inventory, no checksum, no clock and no colour controller; tests that need one stand in for it and say so.
- The test harness runs Home Assistant 2026.10. Entity naming changed in 2026.11; that rule is checked against the 2026.11 source, not on a running 2026.11.

---

## Known limitations

- **One client per bus.** Stop any other Nikobus software before starting.
- **One config entry.** Two buses cannot share one Home Assistant.
- **No auto-discovery of the gateway.** The serial path or `host:port` is entered by hand.
- **Read-only by design.** A module's programming is never written: no restore from a backup. Setting the PC-Link clock is the only write.
- **Names come from the `.nkb`.** The bus carries wiring, not labels.
- **The RGB controller's colour and brightness cannot be set**, and an audio zone's volume level cannot be read: the bus offers neither.
- **Calendar programs stay in the PC-Link.** A calendar channel that drives an output is named in `controlled_by`; its program is neither read nor fired.
- **A press sent by Home Assistant is not echoed.** No event fires for it; the modules it drives are read instead.
- **The refresh interval is fixed**: every two minutes, or every five for what a Feedback Module does not report.

---

## Development

```bash
pip install -r requirements_test.txt   # Python 3.14; Home Assistant and nikobus-simulator
python -m pytest -q                    # about 150 tests, 7 to 8 minutes
ruff check .
```

The code is in `custom_components/nikobus_ng/`: `hub.py` (connection, state, commands), `inventory.py` (the one store), `discovery.py`, `config_flow.py`, one file per platform, `maintenance.py`, `describe.py` and `llm_api.py` (the wiring as data), `takeover.py`. [`CLAUDE.md`](CLAUDE.md) holds the rules the project is developed under.

The design started from a [review of the Nikobus integration](https://github.com/fdebrus/Nikobus-HA/blob/main/documentation/nikobus-ng-review.md). Nikobus NG is about 5 900 lines of Python against 15 000 there.

---

## Issues, discussion & legal

**Bugs and requests:** [GitHub issues](https://github.com/fdebrus/Nikobus_NG/issues). The integration's *Download diagnostics* and a short description are what help most; the diagnostics hold addresses and counts, no names.

**Questions:** the [Home Assistant community thread](https://community.home-assistant.io/t/custom-component-nikobus/732832) of the Nikobus integration.

**Trademark:** Nikobus is a trademark of Niko NV. This project is an independent community effort, not affiliated with, endorsed by, or sponsored by Niko NV.

**License:** [PolyForm Noncommercial License 1.0.0](LICENSE) — you may use, copy, modify and share the software for any **noncommercial** purpose. **Any commercial use requires a separate license from the maintainer.** Provided "as is", without warranties of any kind.
