import socket
import threading
import json
from network.system_logger import system_logger as logger

class NetworkServer:
    def __init__(self, logger=None):
        self.port = None
        self.running = False
        self.server_sock = None
        self.logger = logger

    def configure(self, port):
        self.port = port

    def start(self):
        if not self.port:
            raise ValueError("Port nie został ustawiony.")

        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(("0.0.0.0", self.port))
        self.server_sock.listen()
        self.running = True
        logger.info(f"Serwer nasłuchuje na porcie {self.port}")

        try:
            while self.running:
                self.server_sock.settimeout(1.0)
                try:
                    client_sock, addr = self.server_sock.accept()
                except socket.timeout:
                    continue
                threading.Thread(target=self._handle_client, args=(client_sock, addr), daemon=True).start()
        except Exception as e:
            logger.error(f"Błąd serwera: {e}")
        finally:
            if self.server_sock:
                self.server_sock.close()
            logger.info("Serwer został zatrzymany.")

    def stop(self):
        self.running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception as e:
                logger.error(f"Błąd przy zamykaniu socketu serwera: {e}")

    def _handle_client(self, client_socket: socket.socket, addr):
        logger.info(f"Nowe połączenie: {addr}")
        try:
            buffer = b""
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line.decode())
                        logger.info(f"Odebrano dane od {addr}: {payload}")

                        # Logowanie do Loggera aplikacji
                        if self.logger:
                            from datetime import datetime
                            ts = datetime.fromisoformat(payload["timestamp"])
                            self.logger.log_reading(
                                sensor_id=payload["sensor_id"],
                                timestamp=ts,
                                value=payload["value"],
                                unit=payload["unit"]
                            )

                        client_socket.sendall(b"ACK\n")
                    except json.JSONDecodeError as e:
                        logger.error(f"Błąd JSON od {addr}: {e}")
        except Exception as e:
            logger.error(f"Błąd klienta {addr}: {e}")
        finally:
            client_socket.close()
            logger.info(f"Zamknięto połączenie z {addr}")
