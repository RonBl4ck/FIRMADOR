import os
import sys


ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.ui.streamlit_app import run


if __name__ == "__main__":
    run()
