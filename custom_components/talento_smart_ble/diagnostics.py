async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "version": "2026.11.1",
        "purpose": "GATT inspection and manual channel 1 status test; no relay control",
        "last_attempt": coordinator.last_attempt,
        "last_attempt_success": coordinator.last_update_success,
        "failure_reason": coordinator.failure_reason,
        "last_successful_scan": coordinator.data,
        "status_test": {
            "last_attempt": coordinator.status.last_attempt,
            "last_attempt_success": coordinator.status.last_update_success,
            "failure": coordinator.status.failure,
            "measurement": coordinator.status.data,
            "fresh": coordinator.status.fresh,
            "pin_authentication_implemented": False,
        },
    }
