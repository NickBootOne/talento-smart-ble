async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "version": "2026.10.1",
        "purpose": "GATT metadata inspection only; no relay state or control",
        "last_attempt": coordinator.last_attempt,
        "last_attempt_success": coordinator.last_update_success,
        "failure_reason": coordinator.failure_reason,
        "last_successful_scan": coordinator.data,
    }
