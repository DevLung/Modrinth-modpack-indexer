from sys import argv, exit
from os import path, makedirs, remove, startfile
from shutil import rmtree
from zipfile import ZipFile
from dataclasses import dataclass
import re
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
CONNECTION_ERROR_MSG: str = f"Could not GET data from API"
NO_PROJECT_URL_PLACEHOLDER: str = "about:blank"
MODRINTH_INDEX_PATH: str = "./modrinth.index.json"
OVERRIDE_DIR_PATH: str = "./overrides/"
MRINDEX_NAME_KEY: str = "name"
MRINDEX_VERSION_KEY: str = "versionId"
MRINDEX_SUMMARY_KEY: str = "summary"
MRINDEX_FILES_KEY: str = "files"
MRINDEX_DEPENDENCIES_KEY: str = "dependencies"
MODRINTH_API_VERSION_ENDPOINT: str = "https://api.modrinth.com/v2/version"
MODRINTH_API_PROJECT_ENDPOINT: str = "https://api.modrinth.com/v2/project"
MODRINTH_URL_BASE: str = f"https://modrinth.com"
CONTENTS_INDEX_FILENAME: str = "contents-index.html"
OUTPUT_DIRECTORY_SUFFIX: str = "_index"

@dataclass
class ModrinthFile:
    project_name: str
    project_url: str
    project_type: str
    version: str
    version_download_url: str




def index(pack_file_path: str, output_path: str) -> None:
    if path.exists(output_path):
        if FORCE_ARG not in argv:
            print(OUTPUT_PATH_EXISTS_MSG)
            exit(1)
        rmtree(output_path)
    
    makedirs(output_path)

    print("extracting overrides...")
    
    with ZipFile(pack_file_path, "r") as pack_file:
        pack_file.extractall(output_path)

    print("reading modrinth index...")
    with open(path.join(output_path, MODRINTH_INDEX_PATH), "r") as modrinth_index_file:
        modrinth_index: dict = json.load(modrinth_index_file)
    remove(path.join(output_path, MODRINTH_INDEX_PATH))

    process_index(modrinth_index, output_path)



def get_modrinth_project_info(mrindex_file_object: dict) -> ModrinthFile:
    download_url: str = mrindex_file_object["downloads"][0]
    # extract version id, project id from download url
    version_id: str = re.search(r"(?<=/versions/)[^/]+", download_url).group(0) # type: ignore
    project_id: str = re.search(r"(?<=/data/)[^/]+", download_url).group(0) # type: ignore
    
    try:
        version_info: dict = requests.get(f"{MODRINTH_API_VERSION_ENDPOINT}/{version_id}").json()
        version_name: str = version_info["name"]
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError) as ex:
        if isinstance(ex, requests.exceptions.JSONDecodeError): # usually means the api returned an empty response
            version_name: str = "null"
        else:
            print(f"{CONNECTION_ERROR_MSG} ({ex})")
            exit(1)
    
    try:
        project_info: dict = requests.get(f"{MODRINTH_API_PROJECT_ENDPOINT}/{project_id}").json()
        project_title: str = project_info["title"]
        project_type: str = project_info["project_type"]
        project_slug: str = project_info["slug"]
        project_url: str = f"{MODRINTH_URL_BASE}/{project_type}/{project_slug}"
    except (requests.exceptions.JSONDecodeError, requests.exceptions.ConnectionError) as ex:
        if isinstance(ex, requests.exceptions.JSONDecodeError): # usually means the api returned an empty response
            project_title: str = f"{re.search(r'[^/]+$', download_url).group(0)} (unknown project)" # type: ignore
            # retrieve project type from file's target directory name by removing the "s" at the end
            project_type: str = re.search(r"^[^/]+", mrindex_file_object["path"]).group(0)[:-1] # type: ignore
            project_url: str = NO_PROJECT_URL_PLACEHOLDER
        else:
            print(f"{CONNECTION_ERROR_MSG} ({ex})")
            exit(1)
    
    return ModrinthFile(project_title, project_url, project_type, version_name, download_url)



def create_project_file_tr(file: ModrinthFile) -> str:
    tr: str = "\n                " # indentation
    tr += f"<tr><td style='padding-right: 1rem;'><a href='{file.project_url}' target='_blank' rel='noreferrer noopener'>{file.project_name}</a></td>"
    tr += f"<td><a href='{file.version_download_url}' target='_blank' rel='noreferrer noopener'>{file.version}</a></td></tr>"
    return tr



def create_html_content_index(name: str, version: str, summary: str, dependencies: dict[str, str], contents: dict[str, list[ModrinthFile]], output_path: str) -> None:
    html: str = f"""<!DOCTYPE html>
<html lang='en'>

<head>
    <meta charset='utf-8'>
    <title>{name}: Contents Index</title>
</head>

<body style='font-family: monospace, sans-serif;'>
    <h1>Contents Index</h1>
    
    <div>
        <h2><i>Modpack Name:</i> {name}</h2>
        <table style='text-align: left; margin-bottom: 2.5rem'>
            <tr>
                <th style='padding-right: 2rem'><i>Version</i></th>
                <th style='padding-right: 3rem'><i>Summary</i></th>
                <th><i>Dependencies</i></th>
            </tr>
            <tr>
                <td style='padding-right: 2rem; vertical-align: top;'>{version}</td>
                <td style='padding-right: 3rem; vertical-align: top;'>{summary}</td>
                <td style='vertical-align: top;'>
                    <ul style='padding: 0; margin: 0;'>"""
    
    for dependency, dependency_version in dependencies.items():
        html += f"\n                        <li>{dependency} {dependency_version}</li>"
    
    html += """
                    </ul>
                </td>
            </tr>
        </table>
    </div>

    <div>"""

    for type_name, content_type in contents.items():
        if content_type != []:
            html += f"""
        <p>
            <h3 id='{type_name}s'>{type_name.capitalize()}s</h3>
            <table style='text-align: left; margin-bottom: 3rem'>
                <tr><th><i>Project</i></th><th><i>Version</i></th></tr>"""
            for file in content_type:
                html += create_project_file_tr(file)
            html += """            </table>
        </p>"""
    
    if path.exists(path.join(output_path, OVERRIDE_DIR_PATH)):
        html += f"""
        <p>
            <h3 id='overrides'>Overrides</h3>
            Files manually added to the pack are located <a href='{OVERRIDE_DIR_PATH}' target='_blank' rel='noreferrer noopener'>here</a>
        </p>"""

    html += """
    </div>
</body>

</html>
"""

    with open(path.join(output_path, CONTENTS_INDEX_FILENAME), "w") as file:
        file.write(html)



def process_index(index: dict, output_path: str) -> None:
    pack_name: str = index[MRINDEX_NAME_KEY]
    pack_version: str = index[MRINDEX_VERSION_KEY]
    pack_summary: str = index[MRINDEX_SUMMARY_KEY]
    pack_dependencies: dict[str, str] = index[MRINDEX_DEPENDENCIES_KEY]
    pack_contents: dict[str, list[ModrinthFile]] = {
        "mod": [],
        "datapack": [],
        "resourcepack": [],
        "shader": []
    }
    request_counter: int = 0
    for item in index[MRINDEX_FILES_KEY]:
        request_counter += 1
        print(f"retrieving project info... [{request_counter}/{len(index[MRINDEX_FILES_KEY])}]")
        
        item_data: ModrinthFile = get_modrinth_project_info(item)
        pack_contents[item_data.project_type].append(item_data)

    print("creating contents index...")
    create_html_content_index(pack_name, pack_version, pack_summary, pack_dependencies, pack_contents, output_path)



def main() -> None:
    if len(argv) < 2 or argv[1] in HELP_ARGS:
        print(HELP_MSG)
        exit(1)

    if not path.isfile(argv[1]):
        print(INVALID_INPUT_MSG)
        exit(1)

    input_file: str = path.realpath(argv[1])
    output_location: str = ""
    if len(argv) < 3 or argv[2] == FORCE_ARG:
        output_location = path.dirname(input_file)
    else:
        output_location = path.realpath(argv[2])
    # generate output directory path named based on input_file (without extention)
    output_path: str = path.join(output_location, f"{path.splitext(path.basename(input_file))[0]}{OUTPUT_DIRECTORY_SUFFIX}")

    print(f"starting to index '{input_file}', output will be saved at '{output_path}'...")
    index(input_file, output_path)
    print(f"Done! Output saved at '{output_path}'")
    startfile(output_path)



if __name__ == "__main__":
    main()