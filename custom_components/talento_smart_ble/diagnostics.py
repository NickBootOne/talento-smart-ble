async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "version": "2026.11.9",
        "purpose": "Channel 1 status, FIX/AUTO control and read-only program retrieval; no override or PIN handshake",
        "last_attempt": coordinator.last_attempt,
        "last_attempt_success": coordinator.last_update_success,
        "failure_reason": coordinator.failure_reason,
        "last_successful_scan": coordinator.data,
        "programming": {
            "last_update_success": coordinator.program.last_update_success,
            "failure": coordinator.program.failure,
            "snapshot": coordinator.program.data,
        },
        "status": {
            "last_attempt": coordinator.status.last_attempt,
            "last_attempt_success": coordinator.status.last_update_success,
            "failure": coordinator.status.failure,
            "measurement": coordinator.status.data,
            "fresh": coordinator.status.fresh,
            "freshness_reason": coordinator.status.freshness_reason,
            "measurement_age_seconds": coordinator.status.measurement_age_seconds,
            "poll_interval_seconds": 30,
            "pin_authentication_implemented": False,
            "last_command": coordinator.status.last_command,
        },
    }
