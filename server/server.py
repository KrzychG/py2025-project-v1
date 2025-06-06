import socket
import threading
import json
import logging
from network.config import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class NetworkServer:
    def __init__(self, port: int = None):
        """Inicjalizuje serwer na wskazanym porcie."""
        config = load_config()
        self.port = port or config.get("port", 9000)

    def start(self) -> None:
        """Uruchamia nasłuchiwanie połączeń i obsługę klientów."""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("0.0.0.0", self.port))
        server_sock.listen()
        logger.info(f"Server nasłuchuje na porcie {self.port}")
        try:
            while True:
                client_sock, addr = server_sock.accept()
                threading.Thread(target=self._handle_client, args=(client_sock, addr), daemon=True).start()
        except KeyboardInterrupt:
            logger.info("Zatrzymyanie serwera...")
        finally:
            server_sock.close()

    def _handle_client(self, client_socket: socket.socket, addr) -> None:
        """Odbiera dane, wysyła ACK i wypisuje je na konsolę."""
        logger.info(f"Nowe połączenie: {addr}")
        try:
            buffer = b""
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    logger.info(f"Klient {addr} rozłączył się")
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line.decode())
                        logger.info(f"Odebrano dane od {addr}:")
                        for k, v in payload.items():
                            print(f" {k}: {v}")
                        client_socket.sendall(b"ACK\n")
                    except json.JSONDecodeError as e:
                        logger.error(f"Błąd parsowania JSON: {e}")
        except Exception as e:
            logger.error(f"Błąd przy obsłudze klienta {addr}: {e}")
        finally:
            client_socket.close()
            logger.info(f"Zamknięto połączenie z klientem {addr}")

if __name__ == "__main__":
    config = load_config()
    port = config.get("port", 9000)
    server = NetworkServer(port)
    server.start()
