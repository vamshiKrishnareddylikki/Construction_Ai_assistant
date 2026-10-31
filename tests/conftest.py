"""Lets tests import modules from the src/ folder (e.g. `from clean_data import clean`)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
