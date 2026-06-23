from pathlib import Path
import sys
import json
import os

# try importing config
import config
stashconfig = config.stashconfig if hasattr(config, 'stashconfig') else {
    "scheme": "http",
    "Host":"localhost",
    "Port": "9999",
    "ApiKey": "",
}

try:
    import stashapi.log as log
    from stashapi.stashapp import StashInterface
except ModuleNotFoundError:
    print("You need to install the stashapp-tools (stashapi) python module. (cmd): pip install stashapp-tools", file=sys.stderr)
    sys.exit()

stash = StashInterface(stashconfig)

JSONS_PATH = Path("jsons")

def get_scene_data(fragment_data):
    scene_id = fragment_data["id"]
    scene_title = fragment_data["title"]
    scene_files = []

    response = stash.find_scene(scene_id)

    if response:
        for f in response["files"]:
            scene_files.append(os.path.basename(f["path"]))
        return {"id": scene_id, "title": scene_title, "files": scene_files}
    return {}

def mapValues(scene_data):
    output = {
        "title": "",
        "code" : "",
        "director":"",
        "movies": [],
        "date": "",
        "url": "",
        "image": "",
        "details": "",
        "performers": [],
        "tags": []
    }

    #JSON files should contain a "_source" parameter so we can determine their format
    formatVersion = float(scene_data['_source'].split('_')[-1][7:])

    if formatVersion >= 1:
        output['title'] = scene_data['title']
        output['date'] = scene_data['date'].split('T')[0]
        output['url'] = scene_data['url']
        output['image'] = scene_data['image']
        output['tags'] = list(map(lambda x: {"Name":x}, scene_data['tags']))
        output['studio'] = {"Name" : scene_data['studio'] }
        output['details'] = scene_data['details']
    
    # Schema v1.1 introduces a field for performers
    if formatVersion > 1.1:
        output['performers'] = list(map(lambda x: {"Name":x}, scene_data['performers']))
    return output


if sys.argv[1] == "fragment":
    fragment = json.loads(sys.stdin.read())
    scene = get_scene_data(fragment)
    filename = scene['files'][0][:-3] + "json"
    filename = JSONS_PATH / filename
    try:
        with open(filename, 'rb') as f:
            scene_info = json.load(f)
            print(json.dumps(mapValues(scene_info)))
    except:
        print("{}")
