import math
import random
from Sensors.Sensor import Sensor
from datetime import datetime

class TemperatureSensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        now = datetime.now()
        hour = now.hour

        # Cykl dobowy
        if 0 <= hour < 6:
            base = self.min_value + 1
        elif 6 <= hour < 12:
            base = self.min_value + (self.max_value - self.min_value) * 0.5
        elif 12 <= hour < 18:
            base = self.max_value - 1
        else:  # 18–24
            base = self.min_value + (self.max_value - self.min_value) * 0.3

        # szum
        value = round(base + random.uniform(-1, 1), 2)
        self.last_value = value

        # Wywołanie callbacka
        for callback in self.callbacks:
            callback(self.name, now, value, self.unit)

        return value
