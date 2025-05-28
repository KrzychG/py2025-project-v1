from Logger import Logger
from Sensors.TemperatureSensor import TemperatureSensor
import time

logger = Logger("config.json")
logger.start()

sensor = TemperatureSensor(1, "temp", "°C", -10, 50, 1)
sensor.register_callback(logger.log_reading)

for _ in range(10):
    sensor.read_value()
    time.sleep(sensor.frequency)

logger.stop()
