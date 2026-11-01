COMMANDS = {"AUTO": b"\x00", "FIX_ON": b"\x01", "FIX_OFF": b"\x02"}


def encode_command(command):
    if command not in COMMANDS:
        raise ValueError("unsupported_command")
    return COMMANDS[command]


def command_confirmed(command, measurement):
    if command == "AUTO":
        return measurement["mode"] == "AUTO" and measurement["relay"] is not None
    expected = {"FIX_ON": True, "FIX_OFF": False}
    return command in expected and measurement["mode"] == command and measurement["relay"] is expected[command]


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
