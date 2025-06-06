from datetime import datetime
import socket

class NetworkClient:
    def __init__(self, host, port, timeout=5.0, retries=3, logger=None):
        """Inicjalizuje klienta sieciowego."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.sock = None
        self.logger = logger

    def _log_info(self, msg: str):
        if self.logger:
            self.logger.log_reading(sensor_id="network", timestamp=datetime.now(), value=0, unit="INFO: " + msg)

    def _log_error(self, msg: str):
        if self.logger:
            self.logger.log_reading(sensor_id="network", timestamp=datetime.now(), value=0, unit="ERROR: " + msg)

    def connect(self):
        """Nawiazuje połączenie z serwerem."""
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            self._log_info(f"Połączono z {self.host}:{self.port}")
        except Exception as e:
            self._log_error(f"Błąd połączenia: {e}")
            self.sock = None

    def send(self, data: dict) -> bool:
        """Wysyła dane i czeka na potwierdzenie zwrotne."""
        for attempt in range(self.retries):
            if not self.sock:
                self.connect()
            if not self.sock:
                continue
            try:
                serialized = self._serialize(data) + b"\n"
                self.sock.sendall(serialized)
                self._log_info(f"Wysłano dane: {data}")
                ack = self.sock.recv(1024).decode().strip()
                self._log_info(f"Odebrano potwierdzenie: {ack}")
                if ack == "ACK":
                    return True
            except Exception as e:
                self._log_error(f"Błąd wysyłania (próba {attempt+1}): {e}")
                self.close()
        return False

    def close(self):
        """Zamyka połączenie."""
        if self.sock:
            self.sock.close()
            self.sock = None
            self._log_info("Połączenie zamknięte")

    def _serialize(self, data: dict) -> bytes:
        import json
        return json.dumps(data).encode('utf-8')

    def _deserialize(self, raw: bytes) -> dict:
        import json
        return json.loads(raw.decode('utf-8'))
