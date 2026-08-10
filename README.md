# Grewa for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant integration for **Grewa** water-boost pumps. It connects to the
Grewa cloud API and exposes your pump as a single device with live pressure,
power, energy and status sensors.

## Features

- Full UI setup — no YAML required
- One Home Assistant **device** per pump, with model and serial from the nameplate
- Live sensors, polled every 30 seconds:
  - Pressure, target pressure, start pressure & start-pressure setpoint
  - Power, voltage, energy (with long-term statistics)
  - Water temperature, motor speed, runtime
  - Error code and active fault codes
  - Last reported timestamp
- Binary sensors: **Online** (connectivity) and **Running**
- Automatic re-authentication prompt if your API key changes
- Redacted diagnostics download for troubleshooting

## Installation

### HACS (recommended)

1. In HACS, go to **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/Grewa-water/homeassistant-grewa` with category **Integration**.
3. Search for **Grewa**, install it, and restart Home Assistant.

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
| Pressure | sensor | kPa |
| Target pressure | sensor | kPa |
| Start pressure | sensor | kPa |
| Start pressure setpoint | sensor | % |
| Power | sensor | W |
| Voltage | sensor | V (diagnostic) |
| Water temperature | sensor | °C |
| Motor speed | sensor | rpm |
| Runtime | sensor | h, total increasing |
| Energy | sensor | kWh, total increasing |
| Error code | sensor | diagnostic |
| Faults | sensor | diagnostic |
| Last reported | sensor | timestamp, diagnostic |
| Online | binary_sensor | connectivity |
| Running | binary_sensor | running |

## Contributing

Issues and pull requests are welcome. Run [hassfest] and the HACS action
locally or rely on the bundled GitHub workflow, which validates both on every
push.

[hassfest]: https://developers.home-assistant.io/blog/2020/04/16/hassfest/

## License

[MIT](LICENSE)
