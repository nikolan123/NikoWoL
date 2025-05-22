import socket

def wake_on_lan(mac_bytes):
    """Send a Wake-on-LAN (WoL) magic packet to a given MAC address."""
    if len(mac_bytes) != 6:
        raise ValueError("MAC address must have exactly 6 byte pairs.")

    # Convert the MAC address to a byte format
    mac_bin = bytes(int(byte, 16) for byte in mac_bytes)

    # Create the magic packet (6x 0xFF + 16x MAC address)
    magic_packet = b'\xFF' * 6 + mac_bin * 16

    # Send the packet to the broadcast address
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, ("255.255.255.255", 9))

    print(f"Wake-on-LAN packet sent to: {'-'.join(mac_bytes)}")