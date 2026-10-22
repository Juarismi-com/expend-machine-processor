"""Levanta el processor con la configuracion de test_env.py, sin tocar el env.py real.

    python scripts/local_test/run_processor.py [puerto]
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.modules["env"] = importlib.import_module("test_env")
os.chdir(ROOT)

from app import app  # noqa: E402

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5097
    app.run(host="127.0.0.1", port=port, debug=False)
