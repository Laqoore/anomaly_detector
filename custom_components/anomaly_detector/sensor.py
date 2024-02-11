"""Sensor platform for integration_blueprint."""
from __future__ import annotations

from collections import deque
from statistics import mean, stdev

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .const import DOMAIN
from .coordinator import BlueprintDataUpdateCoordinator
from .entity import AnomalyDetector

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="anomaly_detector",
        name="Anomaly Detector",
        icon="mdi:format-quote-close",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        AnomalyDetectorSensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class AnomalyDetectorSensor(AnomalyDetector, SensorEntity):
    """integration_blueprint Sensor class."""

    def __init__(
        self,
        coordinator: BlueprintDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._history = deque(maxlen=10)  # Store the last 10 data points
        self._anomaly_detected = False

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        # Parse the current data point
        current_data = self.coordinator.data.get("body")

        # Assume current_data is a numerical value; convert and process it
        try:
            current_value = float(current_data)
            self._process_data_point(current_value)
        except ValueError:
            # Handle non-numerical or missing data
            pass

        # Return "Anomaly" or "Normal" based on the detection result
        return "Anomaly" if self._anomaly_detected else "Normal"

    def _process_data_point(self, data_point: float) -> None:
        """Process a new data point for anomaly detection."""
        self._history.append(data_point)
        if len(self._history) >= 3:  # Ensure enough data for analysis
            avg = mean(self._history)
            sigma = stdev(self._history) if len(self._history) > 1 else 0

            # Simple anomaly detection: more than 2 standard deviations from mean
            self._anomaly_detected = abs(data_point - avg) > 2 * sigma
