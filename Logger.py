import csv
import json
import os
import zipfile
from datetime import datetime, timedelta
from typing import Optional, Iterator, Dict
from collections import defaultdict


class Logger:
    def __init__(self, config_path: str):
        """
        Inicjalizuje logger na podstawie pliku JSON.
        :param config_path: Ścieżka do pliku konfiguracyjnego (.json)
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Plik konfiguracyjny '{config_path}' nie został znaleziony.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Błąd parsowania pliku JSON: {e}")

        # zapisanie zawartości pliku konfiguracyjnego
        self.log_dir = config["log_dir"]
        self.filename_pattern = config["filename_pattern"]
        self.buffer_size = config["buffer_size"]
        self.rotate_every_hours = config["rotate_every_hours"]
        self.max_size_mb = config["max_size_mb"]
        self.rotate_after_lines = config.get("rotate_after_lines")
        self.retention_days = config["retention_days"]

        # utworzenie katalogów jeśli nie istnieją
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(os.path.join(self.log_dir, "archive"), exist_ok=True)

        self.current_file = None
        self.current_writer = None
        self.current_filename = ""
        self.last_rotation = datetime.now()
        self.buffer = []
        self.line_count = 0

        # Bufor w pamięci dla ostatnich odczytów
        self.readings = defaultdict(list)

    def start(self) -> None:
        """
        Otwiera nowy plik CSV do logowania. Jeśli plik jest nowy, zapisuje nagłówek.
        """
        self.current_filename = self._get_log_filename()
        filepath = os.path.join(self.log_dir, self.current_filename)
        file_exists = os.path.exists(filepath)

        self.current_file = open(filepath, "a+", newline="")
        self.current_file.seek(0)
        first_line = self.current_file.readline()
        self.current_writer = csv.writer(self.current_file)

        # tylko jeśli plik nie istnieje lub jest pusty, dodaj nagłówek
        if not file_exists or not first_line.strip():
            self.current_writer.writerow(["timestamp", "sensor_id", "value", "unit"])
            self.current_file.flush()

    def _get_log_filename(self):
        return datetime.now().strftime(self.filename_pattern)

    def stop(self) -> None:
        """
        Wymusza zapis bufora i zamyka bieżący plik.
        """
        self._flush()
        if self.current_file:
            self.current_file.close()
            self.current_file = None

    def _flush(self):
        for row in self.buffer:
            self.current_writer.writerow(row)
            self.line_count += 1
        self.current_file.flush()
        self.buffer.clear()

    def log_reading(
        self,
        sensor_id: str,
        timestamp: datetime,
        value: float,
        unit: str
    ) -> None:
        """
        Dodaje wpis do bufora i ewentualnie wykonuje rotację pliku.
        Dodatkowo buforuje dane w pamięci dla GUI.
        """
        # Buforowanie danych w pamięci dla GUI (przechowujemy tylko ostatnie 12h)
        self.readings[sensor_id].append((timestamp, value, unit))
        cutoff = datetime.now() - timedelta(hours=12)
        self.readings[sensor_id] = [r for r in self.readings[sensor_id] if r[0] >= cutoff]

        # Logowanie do pliku
        row = [timestamp.isoformat(), sensor_id, value, unit]
        self.buffer.append(row)

        if len(self.buffer) >= self.buffer_size:
            self._flush()
            self._check_rotation()

    def _check_rotation(self):
        now = datetime.now()
        elapsed = (now - self.last_rotation).total_seconds() / 3600
        file_size_mb = os.path.getsize(self.current_file.name) / (1024 * 1024)

        if (
            elapsed >= self.rotate_every_hours
            or file_size_mb >= self.max_size_mb
            or (self.rotate_after_lines and self.line_count >= self.rotate_after_lines)
        ):
            self._rotate()

    def _rotate(self):
        self.stop()
        archive_dir = os.path.join(self.log_dir, "archive")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{self.current_filename}_{timestamp}"
        archive_path = os.path.join(archive_dir, f"{archive_name}.zip")

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(os.path.join(self.log_dir, self.current_filename), arcname=self.current_filename)

        os.remove(os.path.join(self.log_dir, self.current_filename))
        self._cleanup_old_archives()
        self.last_rotation = datetime.now()
        self.line_count = 0
        self.start()

    def _cleanup_old_archives(self):
        archive_dir = os.path.join(self.log_dir, "archive")
        now = datetime.now()
        for filename in os.listdir(archive_dir):
            filepath = os.path.join(archive_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if (now - file_time).days > self.retention_days:
                    os.remove(filepath)

    def read_logs(
        self,
        start: datetime,
        end: datetime,
        sensor_id: Optional[str] = None
    ) -> Iterator[Dict]:
        """
        Pobiera wpisy z logów zadanego zakresu i opcjonalnie konkretnego czujnika.
        """
        def _parse_csv(fileobj):
            reader = csv.DictReader(fileobj)
            for row in reader:
                row_time = datetime.fromisoformat(row["timestamp"])
                if start <= row_time <= end:
                    if sensor_id is None or row["sensor_id"] == sensor_id:
                        yield {
                            "timestamp": row_time,
                            "sensor_id": row["sensor_id"],
                            "value": float(row["value"]),
                            "unit": row["unit"]
                        }

        # odczyt zarchiwizowanych logów
        archive_dir = os.path.join(self.log_dir, "archive")
        for filename in os.listdir(archive_dir):
            if filename.endswith(".zip"):
                with zipfile.ZipFile(os.path.join(archive_dir, filename), 'r') as zipf:
                    for name in zipf.namelist():
                        with zipf.open(name) as f:
                            yield from _parse_csv(f)

        # odczyt aktualnych logów
        for filename in os.listdir(self.log_dir):
            if filename.endswith(".csv"):
                with open(os.path.join(self.log_dir, filename), "r") as f:
                    yield from _parse_csv(f)

    def get_latest_readings(self):
        result = {}
        for sensor_id, entries in self.readings.items():
            if entries:
                timestamp, value, unit = entries[-1]
                result[sensor_id] = {
                    "last_value": value,
                    "unit": unit,
                    "timestamp": timestamp
                }
        return result

    def get_average(self, sensor_id: str, hours: int):
        if sensor_id not in self.readings:
            return None
        cutoff = datetime.now() - timedelta(hours=hours)
        values = [v for (ts, v, unit) in self.readings[sensor_id] if ts >= cutoff]
        if not values:
            return None
        return sum(values) / len(values)
