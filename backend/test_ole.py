content = bytes.fromhex('d0cf11e0a1b11ae1000000000000000000000000')
print(f"First 4 bytes hex: {content[:4].hex()}")
print(f"Match b'\\xd0\\xcf\\x11\\xe0': {content[:4] == b'\xd0\xcf\x11\xe0'}")
print(f"Match bytes.fromhex('d0cf11e0'): {content[:4] == bytes.fromhex('d0cf11e0')}")
