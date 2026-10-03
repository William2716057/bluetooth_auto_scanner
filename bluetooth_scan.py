import asyncio
import csv
from bleak import BleakScanner
from datetime import datetime
from pathlib import Path


SCAN_DURATION = 60.0
INTERVAL = 660  # change here


def filename():
    now = datetime.now()
    date = now.strftime("%d%m%Y")
    timestamp = now.strftime("%H%M%S")

    return Path(
        f"bluetooth_hacienda_devices({date})({timestamp}).csv"
    )


async def scan_once():

    print("\nScanning for devices...")

    devices = await BleakScanner.discover(
        timeout=SCAN_DURATION,
        return_adv=True
    )

    output_file = filename()

    rows = []

    for address, (device, advertisement) in devices.items():

        name = device.name or "Unknown"

        # Manufacturer information
        manufacturers = []

        for company_id, data in advertisement.manufacturer_data.items():
            manufacturers.append(
                f"0x{company_id:04X}:{data.hex()}"
            )

        # Service UUIDs
        service_uuids = ";".join(
            advertisement.service_uuids
        )

        # Service data
        service_data = []

        for uuid, data in advertisement.service_data.items():
            service_data.append(
                f"{uuid}:{data.hex()}"
            )

        # Distance estimate
        distance = None

        if advertisement.tx_power is not None:
            n = 2.5

            distance = 10 ** (
                (advertisement.tx_power - advertisement.rssi)
                / (10 * n)
            )

        rows.append({
            "timestamp": datetime.now().isoformat(),
            "address": address,
            "name": name,
            "local_name": advertisement.local_name or "",
            "rssi": advertisement.rssi,
            "tx_power": advertisement.tx_power,
            "estimated_distance_m": (
                f"{distance:.2f}"
                if distance is not None
                else ""
            ),
            "service_uuids": service_uuids,
            "manufacturer_data": ";".join(manufacturers),
            "service_data": ";".join(service_data),
        })

    # Write CSV
    fieldnames = [
        "name",
        "address",
        "local_name",
        "rssi",
        "tx_power",
        "service_uuids",
        "estimated_distance_m",
        "manufacturer_data",
        "service_data",
        "timestamp",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Found {len(rows)} devices")
    print(f"Saved: {output_file}")


async def main():

    print("Continuous Bluetooth scanner")
    print("Scanning every 10 minutes.")
    print("Press Ctrl+C to stop.\n")

    while True:

        try:
            await scan_once()

        except Exception as e:
            print(f"Scan error: {e}")

        print("\nWaiting 10 minutes...")

        await asyncio.sleep(INTERVAL)


try:
    asyncio.run(main())

except KeyboardInterrupt:
    print("\nStopped.")