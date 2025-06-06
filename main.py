import time
from datetime import datetime
from Sensors.PressureSensor import PressureSensor
from Sensors.HumiditySensor import HumiditySensor
from Sensors.AirQualitySensor import AirQualitySensor
from Sensors.TemperatureSensor import TemperatureSensor
from Logger import Logger
from network.client import NetworkClient

# Inicjalizacja loggera
logger = Logger("config.json")
logger.start()

# Inicjalizacja klienta sieciowego
client = NetworkClient(host="127.0.0.1", port=9000, logger=logger)
client.connect()


# Callback do logowania i wysyłki
def log_callback(sensor_id, timestamp, value, unit):
    if isinstance(timestamp, datetime):
        timestamp_str = timestamp.isoformat()
    else:
        timestamp_str = timestamp

    logger.log_reading(sensor_id, timestamp, value, unit)

    data = {
        "sensor_id": sensor_id,
        "timestamp": timestamp_str,
        "value": value,
        "unit": unit
    }
    success = client.send(data)
    if not success:
        print("[ERROR] Nie udało się wysłać danych do serwera.")


# Inicjalizacja czujników
sensors = [
    PressureSensor("P01", "PressureSensor", "hPa", 950, 1050),
    HumiditySensor("H01", "HumiditySensor", "%", 0, 100),
    AirQualitySensor("A01", "AirQualitySensor", "AQI", 0, 500),
    TemperatureSensor("T01", "TemperatureSensor", '\u00B0' "C", -20, 50)
]

for sensor in sensors:
    sensor.register_callback(log_callback)

try:
    while True:
        for sensor in sensors:
            try:
                sensor.read_value()
            except Exception as e:
                print(f"[ERROR] {e}")
        time.sleep(1)

except KeyboardInterrupt:
    print("Zakończono działanie programu.")
    logger.stop()
    client.close()
