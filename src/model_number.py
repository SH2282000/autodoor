import asyncio
from bleak import BleakClient

address = "C0:2C:5C:8D:37:D8"
MODEL_NBR_UUID = "180A"

async def main(address):
    async with BleakClient(address) as client:
        model_number = await client.read_gatt_char(MODEL_NBR_UUID)
        print("Model Number: {0}".format("".join(map(chr, model_number))))

asyncio.run(main(address))
