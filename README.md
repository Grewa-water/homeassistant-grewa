# Grewa for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant integration for **Grewa** water-boost pumps. It connects to the
Grewa cloud API and exposes your pump as a single device with live pressure,
power, energy and status sensors.

## Features

- Full UI setup — no YAML required
- One Home Assistant **device** per pump, with model and serial from the nameplate
- Live sensors, polled every 30 seconds:
  - Pump status — **Off**, **Standby** or **Running**, matching the Grewa app
  - Current pressure, set pressure, cut-in pressure & cut-in point
  - Power, voltage, water temperature, motor speed, power-on time
  - Error code and active fault codes
  - Last reported timestamp
- Binary sensors: **Online**, **Running** (motor turning) and **Power switch**
- Automatic re-authentication prompt if your API key changes
- Redacted diagnostics download for troubleshooting

## Installation

### HACS (recommended)

1. Open **HACS** from the Home Assistant sidebar (not Settings → Devices &
   Services → HACS, which is only the integration's own settings).
2. Go to **⋮ → Custom repositories**, add
   `https://github.com/Grewa-water/homeassistant-grewa` with category
   **Integration**, and click **Add**.
3. Search for **Grewa**, open it, click **Download**, then restart Home
   Assistant when prompted.

The Grewa entry shows a placeholder image in the HACS store list. That is
expected for every custom integration — HACS reads store icons from the
Home Assistant brands CDN, which no longer accepts custom integrations. The
Grewa icon appears normally everywhere inside Home Assistant itself.

### Manual

Copy `custom_components/grewa` into your Home Assistant `config/custom_components`
directory and restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Grewa**.
3. Enter your **Device ID** and **API key** (from the Grewa portal).

That's it — your pump appears as a device with all its sensors.

### Finding your credentials

- **Device ID** — the UUID of your pump in the Grewa portal.
- **API key** — a personal key beginning with `gk_`. It is sent as a
  `Bearer` token; you only paste the key itself.

## Entities

| Entity | Type | Notes |
| --- | --- | --- |
| Status | sensor | Off / Standby / Running |
| Current pressure | sensor | kPa |
| Set pressure | sensor | kPa |
| Cut-in pressure | sensor | kPa |
| Cut-in point | sensor | % |
| Power | sensor | W |
| Voltage | sensor | V (diagnostic) |
| Water temperature | sensor | °C |
| Motor speed | sensor | rpm |
| Power-on time | sensor | h, total increasing — hours powered, not motor hours |
| Error code | sensor | diagnostic |
| Faults | sensor | diagnostic |
| Last reported | sensor | timestamp, diagnostic |
| Online | binary_sensor | connectivity |
| Running | binary_sensor | motor turning |
| Power switch | binary_sensor | mains power on (standby vs off) |

Pressures are shown in **bar**, matching the pump's display and the Grewa
app. They are recorded in kPa, so if you prefer a different unit open any
pressure entity's settings and pick **kPa**, **psi** or another — it changes
the display without affecting stored history.

The integration is read-only: it monitors the pump but cannot control it,
because Grewa API keys are deliberately not permitted to write.

## Contributing

Issues and pull requests are welcome. Run [hassfest] and the HACS action
locally or rely on the bundled GitHub workflow, which validates both on every
push.

[hassfest]: https://developers.home-assistant.io/blog/2020/04/16/hassfest/

## License

[MIT](LICENSE)
