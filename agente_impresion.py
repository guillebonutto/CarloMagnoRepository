"""
Agente local de impresión directa para Xprinter XP-365B (58x34mm TSPL).
Ejecutar en la PC Windows donde está conectada la impresora:
    python agente_impresion.py
Escucha en http://127.0.0.1:9100/imprimir
"""
import ctypes
from ctypes import wintypes
import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer


def buscar_xprinter():
    try:
        res = subprocess.run(
            ['powershell', '-NoProfile', '-Command', 'Get-Printer | Select-Object -ExpandProperty Name'],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode == 0:
            printers = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            for p in printers:
                if '365' in p.lower() or 'xprinter' in p.lower():
                    return p
    except Exception:
        pass
    return 'Xprinter XP-365B'


def enviar_raw_windows(printer_name, raw_bytes):
    winspool = ctypes.WinDLL('winspool.drv', use_last_error=True)

    class DOC_INFO_1(ctypes.Structure):
        _fields_ = [
            ('pDocName', wintypes.LPWSTR),
            ('pOutputFile', wintypes.LPWSTR),
            ('pDatatype', wintypes.LPWSTR),
        ]

    h_printer = wintypes.HANDLE()
    if not winspool.OpenPrinterW(printer_name, ctypes.byref(h_printer), None):
        raise RuntimeError(f"No se pudo abrir la impresora '{printer_name}' (código {ctypes.get_last_error()}).")

    try:
        doc_info = DOC_INFO_1()
        doc_info.pDocName = 'Etiquetas 58x34mm'
        doc_info.pOutputFile = None
        doc_info.pDatatype = 'RAW'

        job_id = winspool.StartDocPrinterW(h_printer, 1, ctypes.byref(doc_info))
        if job_id == 0:
            raise RuntimeError(f"StartDocPrinterW falló (código {ctypes.get_last_error()}).")
        try:
            if not winspool.StartPagePrinter(h_printer):
                raise RuntimeError(f"StartPagePrinter falló (código {ctypes.get_last_error()}).")
            try:
                written = wintypes.DWORD(0)
                buf = ctypes.create_string_buffer(raw_bytes)
                if not winspool.WritePrinter(h_printer, buf, len(raw_bytes), ctypes.byref(written)):
                    raise RuntimeError(f"WritePrinter falló (código {ctypes.get_last_error()}).")
            finally:
                winspool.EndPagePrinter(h_printer)
        finally:
            winspool.EndDocPrinter(h_printer)
    finally:
        winspool.ClosePrinter(h_printer)


class PrintHandler(BaseHTTPRequestHandler):
    def _send_cors(self, status=200):
        self.send_response(status)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()

    def do_OPTIONS(self):
        self._send_cors(204)

    def do_POST(self):
        if self.path != '/imprimir':
            self._send_cors(404)
            self.wfile.write(json.dumps({'success': False, 'error': 'Ruta no encontrada'}).encode('utf-8'))
            return

        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8'))
            raw_tspl = body.get('raw_tspl', '')
            if not raw_tspl:
                self._send_cors(400)
                self.wfile.write(json.dumps({'success': False, 'error': 'Falta raw_tspl'}).encode('utf-8'))
                return

            printer_name = body.get('printer') or buscar_xprinter()
            enviar_raw_windows(printer_name, raw_tspl.encode('ascii', errors='replace'))

            self._send_cors(200)
            self.wfile.write(json.dumps({
                'success': True,
                'mensaje': f'Etiquetas enviadas directo a {printer_name}.'
            }).encode('utf-8'))
        except Exception as e:
            self._send_cors(500)
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))


if __name__ == '__main__':
    print('Agente de impresion Xprinter XP-365B escuchando en http://127.0.0.1:9100')
    print('Impresora detectada:', buscar_xprinter())
    HTTPServer(('127.0.0.1', 9100), PrintHandler).serve_forever()
