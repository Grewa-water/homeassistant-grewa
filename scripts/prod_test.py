"""End-to-end test of the Grewa integration against the live API.

Drives the real config flow, coordinator and both platforms inside a real
Home Assistant instance, then dumps every entity it produced. Exits non-zero
if any entity fails to report a usable value.

Setup (Home Assistant needs Python 3.13+):

    uv venv --python 3.13 .venv
    uv pip install --python .venv/bin/python \
        homeassistant pytest-homeassistant-custom-component

Credentials are read from grewa.env in the repo root (gitignored):

    GREWA_DEVICE_ID=<uuid>
    GREWA_API_KEY=gk_...

Usage:

    .venv/bin/python scripts/prod_test.py [base_url]
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
from contextlib import AsyncExitStack
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENV_FILE = REPO / "grewa.env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, _, value = line.partition("=")
            os.environ.setdefault(name.strip(), value.strip().strip("'\""))

try:
    DEVICE_ID = os.environ["GREWA_DEVICE_ID"]
    API_KEY = os.environ["GREWA_API_KEY"]
except KeyError as err:
    sys.exit(f"missing {err.args[0]} — set it in {ENV_FILE} or the environment")

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://api.grewa.com.au"

# Values that mean "this entity did not report anything usable". The faults
# sensor legitimately reports the string "None" when fault_codes is empty.
NO_VALUE = {"unknown", "unavailable", "<no state>"}


def redact(value: str) -> str:
    """Render a secret safely for logs."""
    return f"{value[:6]}…{value[-4:]}" if len(value) > 12 else "…"


async def main() -> int:
    """Run the integration against the live API and report on every entity."""
    config_dir = Path(tempfile.mkdtemp(prefix="grewa-prod-test-"))
    shutil.copytree(
        REPO / "custom_components/grewa", config_dir / "custom_components/grewa"
    )

    from homeassistant import config_entries, loader
    from homeassistant.const import __version__
    from pytest_homeassistant_custom_component.common import async_test_home_assistant

    print(f"Home Assistant {__version__}")
    print(f"base_url   {BASE_URL}")
    print(f"device_id  {DEVICE_ID}")
    print(f"api_key    {redact(API_KEY)}\n")

    stack = AsyncExitStack()
    hass = await stack.enter_async_context(
        async_test_home_assistant(config_dir=str(config_dir))
    )
    # Equivalent of the enable_custom_integrations fixture: forces a rescan of
    # config_dir/custom_components instead of the empty cached set.
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)

    integration = await loader.async_get_integration(hass, "grewa")
    print(f"loaded     {integration.name} v{integration.version}\n")

    # HA's shared client session builds a zeroconf-backed DNS resolver, which
    # needs the network integration loaded first.
    from homeassistant.setup import async_setup_component

    await async_setup_component(hass, "network", {})

    # --- 1. Raw API probe -------------------------------------------------
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    sys.path.insert(0, str(config_dir / "custom_components"))
    from grewa.api import GrewaApiClient  # type: ignore[import-not-found]

    client = GrewaApiClient(async_get_clientsession(hass), API_KEY, BASE_URL)
    print("=== raw GET /api/v1/devices/{id} ===")
    device = await client.async_get_device(DEVICE_ID)
    print(json.dumps(device, indent=2, default=str))
    print("\n=== raw GET /api/v1/devices/{id}/live-read ===")
    print(json.dumps(await client.async_get_live(DEVICE_ID), indent=2, default=str))

    # --- 2. Real config flow ---------------------------------------------
    print("\n=== config flow ===")
    result = await hass.config_entries.flow.async_init(
        "grewa", context={"source": config_entries.SOURCE_USER}
    )
    print(f"step       {result['type']} / {result.get('step_id')}")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"device_id": DEVICE_ID, "api_key": API_KEY, "base_url": BASE_URL},
    )
    if result["type"] != "create_entry":
        print(f"FAILED     {result['type']} errors={result.get('errors')}")
        return 1
    print(f"created    title={result['title']!r}")
    await hass.async_block_till_done()

    entry = hass.config_entries.async_entries("grewa")[0]
    print(f"entry      state={entry.state}")
    if entry.state is not config_entries.ConfigEntryState.LOADED:
        print(f"FAILED     {entry.reason}")
        return 1

    # --- 3. Device + entities --------------------------------------------
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    print("\n=== device registry ===")
    for dev in dr.async_get(hass).devices.get_devices_for_config_entry_id(
        entry.entry_id
    ):
        print(f"  name         {dev.name}")
        print(f"  manufacturer {dev.manufacturer}")
        print(f"  model        {dev.model}  model_id={dev.model_id}")
        print(f"  serial       {'<set>' if dev.serial_number else '<none>'}")

    entities = er.async_get(hass).entities.get_entries_for_config_entry_id(
        entry.entry_id
    )
    print(f"\n=== entities ({len(entities)}) ===")
    bad = []
    for ent in sorted(entities, key=lambda e: e.entity_id):
        state = hass.states.get(ent.entity_id)
        value = state.state if state else "<no state>"
        unit = state.attributes.get("unit_of_measurement", "") if state else ""
        flag = ""
        if value in NO_VALUE:
            flag = "  <-- PROBLEM"
            bad.append((ent.entity_id, value))
        print(f"  {ent.entity_id:<48} {value:>26} {unit:<5}{flag}")

    # --- 4. Diagnostics ---------------------------------------------------
    from grewa.diagnostics import (  # type: ignore[import-not-found]
        async_get_config_entry_diagnostics,
    )

    print("\n=== diagnostics (redaction check) ===")
    text = json.dumps(
        await async_get_config_entry_diagnostics(hass, entry), indent=2, default=str
    )
    leaked = [s for s in (API_KEY, device.get("serial")) if s and s in text]
    if leaked:
        print(f"LEAK       {len(leaked)} secret(s) present in diagnostics output")
        bad.append(("diagnostics", "leaked secrets"))
    else:
        print("redaction  OK — no secrets in output")

    # --- 5. Second poll ---------------------------------------------------
    print("\n=== forced refresh ===")
    await entry.runtime_data.async_refresh()
    success = entry.runtime_data.last_update_success
    print(f"success    {success}")
    if not success:
        bad.append(("coordinator", "refresh failed"))

    print("\n" + "=" * 60)
    if bad:
        print(f"RESULT: {len(bad)} problem(s):")
        for name, value in bad:
            print(f"  - {name}: {value}")
    else:
        print(f"RESULT: all {len(entities)} entities reported values.")

    await stack.aclose()
    shutil.rmtree(config_dir, ignore_errors=True)
    return 1 if bad else 0


sys.exit(asyncio.run(main()))
