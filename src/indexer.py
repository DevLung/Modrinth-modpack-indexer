from sys import argv
from zipfile import ZipFile
import requests
import json



HELPMSG: str = """
Usage:
    indexer.py INPUTFILE OUTPUTPATH
Arguments:
    INPUTFILE   Modpack to be indexed
    OUTPUTPATH  Path where mod index and extracted overrides are to be saved
"""



if __name__ == "__main__":
    if len(argv) > 2 or argv[1] in ["-?", "--help"]:
        print(HELPMSG)