import random
import math
from Sensors.Sensor import Sensor
from datetime import datetime

class PressureSensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)
        self.base_pressure = (min_value + max_value) / 2
        self.trend = 0.02
        self.noise_level = 0.3
        self.time_counter = 0

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        # Symulacja dziennego cyklu wahań ciśnienia
        daily_cycle = math.sin(self.time_counter / 50.0) * 1.5  # amplituda ~1.5 hPa

        # trend i losowy szum
        trend_component = self.trend * self.time_counter
        noise = random.uniform(-self.noise_level, self.noise_level)

        value = self.base_pressure + daily_cycle + trend_component + noise

        value = max(min(value, self.max_value), self.min_value)

        self.last_value = value
        self.time_counter += 1

        # Wywołanie callbacka
        for callback in self.callbacks:
            callback(self.sensor_id, datetime.now(), value, self.unit)

        return value
