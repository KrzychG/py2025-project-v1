import random
from main import Sensor

class TemperatureSensor(Sensor):
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        super().__init__(sensor_id, name, unit, min_value, max_value, frequency)

    def read_value(self):

        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")

        value = random.uniform(self.min_value, self.max_value)
        self.last_value = value
        return value


sensor = TemperatureSensor(1, "czujnik temperatury", "stopnie Celsjusza",
                            -20, 50, 1)
