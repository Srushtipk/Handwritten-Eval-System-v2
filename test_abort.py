import ctypes
import requests

def crash_worker():
    # simulate a C extension segfault/abort
    ctypes.string_at(0)

# We don't actually need to run Flask, we know PyMuPDF can crash.
