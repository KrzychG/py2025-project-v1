import math
import random
from Sensors.Sensor import Sensor
from datetime import datetime

class TemperatureSensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)
        self.base_temp = (min_value + max_value) / 2
        self.variation = (max_value - min_value) / 2
        self.noise_level = 0.8
        self.trend = 0.005
        self.time_counter = 0

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        now = datetime.now()
        hour = now.hour + now.minute / 60.0  # uwzględniamy dokładniejszy czas

        # Cykl dobowy temperatury (sinus: min nocą, max ok. 14:00)
        daily_cycle = math.sin((hour - 6) / 24 * 2 * math.pi)

        # Wahania dzienne (amplituda dostosowana do zakresu)
        temperature = self.base_temp + self.variation * daily_cycle

        temperature += self.trend * self.time_counter

        # Losowy szum
        noise = random.uniform(-self.noise_level, self.noise_level)
        temperature += noise

        temperature = round(max(min(temperature, self.max_value), self.min_value), 2)

        self.last_value = temperature
        self.time_counter += 1

        # Wywołanie callbacka
        for callback in self.callbacks:
            callback(self.sensor_id, now, temperature, self.unit)

        return temperature
