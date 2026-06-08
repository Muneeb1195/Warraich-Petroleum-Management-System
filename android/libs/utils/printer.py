import socket

from libs.utils.escpos import format_receipt


class NetworkPrinter:
    def __init__(self, host, port=9100):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self, timeout=5):
        self.sock = socket.create_connection((self.host, self.port), timeout=timeout)

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def write(self, data):
        if not self.sock:
            raise RuntimeError("Printer not connected")
        self.sock.sendall(data)

    def print_receipt(self, sale_data, business_info):
        data = format_receipt(sale_data, business_info)
        self.write(data)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
