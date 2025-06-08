import random
import math
from Sensors.Sensor import Sensor
from datetime import datetime

class HumiditySensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)
        self.base_humidity = (min_value + max_value) / 2
        self.trend = 0.01
        self.noise_level = 1.5
        self.time_counter = 0

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        # Symulacja dziennego cyklu wilgotności (np. więcej wilgoci nocą)
        daily_cycle = math.cos(self.time_counter / 40.0) * 10

        # Powolna zmiana trendu w tle
        trend_component = self.trend * self.time_counter

        # Losowy szum
        noise = random.uniform(-self.noise_level, self.noise_level)

        value = self.base_humidity + daily_cycle + trend_component + noise

        value = max(min(value, self.max_value), self.min_value)

        self.last_value = value
        self.time_counter += 1

        # Wywołanie callbacka
        for callback in self.callbacks:
            callback(self.sensor_id, datetime.now(), value, self.unit)

        return value
