"""Inicia un servidor temporal, verifica HTTP y navegador y lo detiene al terminar."""
from pathlib import Path
import subprocess
import sys


def main():
    Path('evidence').mkdir(exist_ok=True)
    with Path('evidence/server-log.txt').open('w') as log:
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
            '--port', '8765', '--no-access-log',
        ], stdout=log, stderr=subprocess.STDOUT)
        try:
            subprocess.run([sys.executable, '-m', 'scripts.smoke', '--base-url', 'http://127.0.0.1:8765',
                            '--output', 'evidence/http-local.json'], check=True)
            subprocess.run([sys.executable, '-m', 'scripts.browser_check', '--base-url', 'http://127.0.0.1:8765'], check=True)
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    main()
