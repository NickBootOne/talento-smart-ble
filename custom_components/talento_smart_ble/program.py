MEMORY_SERVICE = "ec04000a-04da-47e5-add4-8ed1c9d52fec"
DIRECTION = "ec04000b-04da-47e5-add4-8ed1c9d52fec"
PACKAGE_COUNT = "ec04000c-04da-47e5-add4-8ed1c9d52fec"
CONTENT = "ec04000e-04da-47e5-add4-8ed1c9d52fec"
MAX_PACKETS = 2048
WEEKDAYS = ["zo", "ma", "di", "wo", "do", "vr", "za"]


def text(value):
    return value.split(b"\x00", 1)[0].decode("cp1252", errors="replace")


def clock(value):
    hours, minutes = value[0] & 31, value[1] & 63
    seconds = value[2] & 63 if len(value) == 3 else 0
    if hours > 23 or minutes > 59 or seconds > 59 or value[0] & 224:
        raise ValueError("unsupported_time_encoding")
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def date_parts(value):
    year, month, day = value
    if month != 255 and not 1 <= month <= 12 or not 1 <= day <= 31:
        raise ValueError("invalid_program_date")
    return {"year": None if year == 255 else 1900 + year, "month": None if month == 255 else month, "day": day}


def decode_rule(packet):
    action = {16: "AAN", 8: "UIT", 4: "PULS", 2: "CYCLUS", 17: "WILLEKEURIG_AAN", 9: "WILLEKEURIG_UIT"}.get(packet[2] & 31)
    time_type = {0: "TIJD", 64: "ZONSOPKOMST", 32: "ZONSONDERGANG"}.get(packet[2] & 96)
    if action is None or time_type is None:
        raise ValueError("unknown_rule_type")
    rule = {
        "action": action, "time_type": time_type,
        "channels": [index + 1 for index in range(8) if packet[3] & (1 << index)],
        "weekdays": [name for index, name in enumerate(WEEKDAYS) if packet[5] & (1 << index)],
        "offset_raw": int.from_bytes(packet[4:5], "little", signed=True),
        "astro_flags_hex": f"{packet[0] & 224:02x}",
    }
    if time_type == "TIJD":
        rule["time"] = clock(packet[6:8])
    if action in ("PULS", "CYCLUS"):
        rule["duration"] = clock(packet[8:11])
        rule["pause"] = clock(packet[11:14])
    return rule


def decode_program(packets):
    programs = {}
    warnings = []
    channel_names = []
    for index, packet in enumerate(packets):
        if len(packet) != 14:
            raise ValueError("expected_14_byte_program_packet")
        kind = packet[0] & 28
        identifier = ((packet[0] & 1) << 8) | packet[1]
        if kind == 0:
            if identifier in programs:
                raise ValueError("duplicate_program_header")
            programs[identifier] = {
                "id": identifier, "name": text(packet[2:13]), "priority": packet[13],
                "date_ranges": [], "rules": [], "date_range_flag": bool(packet[0] & 2),
            }
            if any(value >= 128 for value in packet[2:13]):
                warnings.append({"packet": index, "reason": "name_encoding_requires_verification"})
        elif kind == 12:
            channel_names.append({"channel_raw": packet[1], "name": text(packet[2:])})
    for index, packet in enumerate(packets):
        kind = packet[0] & 28
        identifier = ((packet[0] & 1) << 8) | packet[1]
        if kind in (0, 12):
            continue
        program = programs.get(identifier)
        if program is None:
            warnings.append({"packet": index, "reason": "missing_program_header"})
            continue
        if kind == 4:
            try:
                program["date_ranges"].append({"start": date_parts(packet[2:5]), "end": date_parts(packet[5:8])})
            except ValueError as error:
                warnings.append({"packet": index, "reason": str(error)})
        elif kind == 8:
            try:
                program["rules"].append(decode_rule(packet))
                if packet[0] & 224:
                    warnings.append({"packet": index, "reason": "astro_correction_flags_not_interpreted"})
            except ValueError as error:
                warnings.append({"packet": index, "reason": str(error)})
        else:
            warnings.append({"packet": index, "reason": "unknown_packet_type"})
    overview = []
    for program in programs.values():
        for rule in program["rules"]:
            moment = rule.get("time", rule["time_type"])
            offset = f" (offset {rule['offset_raw']:+}, ruw)" if rule["time_type"] != "TIJD" else ""
            overview.append(f"{program['name'][:20]}: {','.join(rule['weekdays'])} {moment}{offset} {rule['action']} kanaal {','.join(map(str, rule['channels']))}")
        if program["date_range_flag"] and not program["date_ranges"]:
            warnings.append({"program": program["id"], "reason": "date_range_flag_without_decoded_range"})
    summaries = [
        {"id": item["id"], "name": item["name"], "priority": item["priority"], "rule_count": len(item["rules"]), "date_ranges": item["date_ranges"][:2], "date_ranges_truncated": len(item["date_ranges"]) > 2}
        for item in list(programs.values())[:20]
    ]
    return {
        "program_count": len(programs), "rule_count": sum(len(item["rules"]) for item in programs.values()),
        "programs": list(programs.values()), "channel_names": channel_names,
        "complete": not warnings, "warnings": warnings,
        "overview": overview[:30], "overview_truncated": len(overview) > 30,
        "program_summaries": summaries, "program_summaries_truncated": len(programs) > 20,
        "raw_packets": [packet.hex() for packet in packets],
    }
