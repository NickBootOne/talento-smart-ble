def decode_status(payload):
    if len(payload) != 1:
        raise ValueError("expected_one_status_byte")
    value = payload[0]
    states = {
        0: ("AUTO", False),
        1: ("AUTO", True),
        2: ("FIX_ON", True),
        3: ("FIX_OFF", False),
        4: ("OVR", True),
        5: ("OVR", False),
    }
    mode, relay = states.get(value, (None, None))
    return {"raw_hex": payload.hex(), "mode": mode, "relay": relay}
