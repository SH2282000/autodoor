import asyncio
from bleak import BleakClient, BleakScanner
import platform

async def pair_and_connect(device_address_or_name):
    # First, discover the device
    print("Scanning for devices...")
    devices = await BleakScanner.discover(timeout=10.0)
    
    target_device = None
    for device in devices:
        if (device.address == device_address_or_name or 
            (device.name and device_address_or_name.lower() in device.name.lower())):
            target_device = device
            break
    
    if not target_device:
        print(f"Device '{device_address_or_name}' not found")
        return False
    
    print(f"Found device: {target_device.name} ({target_device.address})")
    
    # Connect and pair
    async with BleakClient(target_device.address) as client:
        try:
            # Connection automatically handles pairing for BLE devices
            is_connected = await client.is_connected()
            print(f"Connected: {is_connected}")
            
            if is_connected:
                print("Successfully paired and connected!")
                
                # Optional: Read device info
                services = await client.get_services()
                print(f"Available services: {len(services.services)}")
                
                return True
                
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

# Usage
async def main():
    # Use device name or MAC address
    device_identifier = "E0:4E:7A:AC:8D:A3"  # or "XX:XX:XX:XX:XX:XX"
    success = await pair_and_connect(device_identifier)
    
    if success:
        print("Pairing completed successfully!")
    else:
        print("Pairing failed!")

# Run the pairing process
asyncio.run(main())
