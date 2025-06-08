import random
import math
from Sensors.Sensor import Sensor
from datetime import datetime

class AirQualitySensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)
        self.base_quality = (min_value + max_value) / 2
        self.trend = 0.05
        self.noise_level = 2.0
        self.time_counter = 0

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        # Symulacja dziennego cyklu (np. ruch uliczny rano i wieczorem)
        daily_cycle = math.sin(self.time_counter / 20.0) * 7 + math.sin(self.time_counter / 10.0) * 5

        trend_component = self.trend * (self.time_counter / 100.0)

        # Dodanie szumu
        noise = random.uniform(-self.noise_level, self.noise_level)

        value = self.base_quality + daily_cycle + trend_component + noise

        value = max(min(value, self.max_value), self.min_value)

        self.last_value = value
        self.time_counter += 1

        # Wywołanie callbacka
        for callback in self.callbacks:
            callback(self.sensor_id, datetime.now(), value, self.unit)

        return value
