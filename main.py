import time
from Sensors.PressureSensor import PressureSensor
from Sensors.HumiditySensor import HumiditySensor
from Sensors.AirQualitySensor import AirQualitySensor
from Logger import Logger
from Sensors.TemperatureSensor import TemperatureSensor

logger = Logger("config.json")
logger.start()

# Callback do logowania odczytów
def log_callback(sensor_id, timestamp, value, unit):
    logger.log_reading(sensor_id, timestamp, value, unit)

# Inicjalizacja czujników
sensors = [
    PressureSensor("P01", "PressureSensor", "hPa", 950, 1050),
    HumiditySensor("H01", "HumiditySensor", "%", 0, 100),
    AirQualitySensor("A01", "AirQualitySensor", "AQI", 0, 500),
    TemperatureSensor("T01", "TemperatureSensor", '\u00B0' "C", -20, 50)
]

try:
    while True:
        for sensor in sensors:
            sensor.register_callback(log_callback)
            try:
                sensor.read_value()
            except Exception as e:
                print(f"[ERROR] {e}")
        time.sleep(1)
except KeyboardInterrupt:
    print("Zakończono działanie programu.")
    logger.stop()
