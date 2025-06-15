from sys import argv, exit
from os import path, makedirs, remove
from shutil import rmtree
from zipfile import ZipFile
import requests
import json



HELP_ARGS: list[str] = ["-?", "--help"]
FORCE_ARG: str = "--force"
HELP_MSG: str = """
Usage:
    indexer.py INPUTFILE [OUTPUTLOC]
Arguments:
    INPUTFILE   Modpack to be indexed
    OUTPUTLOC   Location where folder with mod index and extracted overrides is to be saved. If omitted, folder will be saved next to INPUTFILE
"""
INVALID_INPUT_MSG: str = "Please supply a valid modrinth modpack file"
OUTPUT_PATH_EXISTS_MSG: str = f"Output folder already exists. Use {FORCE_ARG} to overwrite it."
MODRINTH_INDEX_PATH: str = "./modrinth.index.json"




def index(pack_file_path: str, output_path: str) -> None:
    if path.exists(output_path):
        if FORCE_ARG not in argv:
            print(OUTPUT_PATH_EXISTS_MSG)
            exit(1)
        rmtree(output_path)
    
    makedirs(output_path)

    with ZipFile(pack_file_path, "r") as pack_file:
        pack_file.extractall(output_path)

    with open(path.join(output_path, MODRINTH_INDEX_PATH), "r") as modrinth_index_file:
        modrinth_index: dict = json.load(modrinth_index_file)

    process_index(modrinth_index)



def process_index(index: dict) -> None:
    pass



def main() -> None:
    if len(argv) < 2 or argv[1] in HELP_ARGS:
        print(HELP_MSG)
        exit(1)

    if not path.isfile(argv[1]):
        print(INVALID_INPUT_MSG)
        exit(1)

    input_file: str = path.realpath(argv[1])
    output_location: str = ""
    if len(argv) < 3 or not path.exists(argv[2]):
        output_location = path.dirname(input_file)
    else:
        output_location = path.realpath(argv[2])
    # generate output directory path named based on input_file (without extention)
    output_path: str = path.join(output_location, path.splitext(path.basename(input_file))[0])

    index(input_file, output_path)



if __name__ == "__main__":
    main()