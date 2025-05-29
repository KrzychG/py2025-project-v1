import random
from Sensors.Sensor import Sensor
from datetime import datetime

class AirQualitySensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        value = random.uniform(self.min_value, self.max_value)
        self.last_value = value

        # Wywołanie callbacka
        for callback in self.callbacks:
            callback(self.name, datetime.now(), value, self.unit)

        return value
