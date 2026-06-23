import json
import os
import sys
import datetime
import codecs
import traceback
import re
import shutil
from pathlib import Path

from py_common import graphql
from py_common import log

## This scraper assumes that the JSON files are stored in the same directory as the video files,
## with the same name, but with .info.json or .json extensions. You can add a second directory to check
## for JSON files here. JSON file names here must match the original media file name, but with a
## .info.json or .json extension. JSON files will be taken from the media's folder first, and if not
## present there a suitably named JSON file in the below directory will be used.
## Image Scraper
## Code,Date,Details,Director,Groups,Image,Performers (see Performer fields),Studio (see Studio Fields),Tags (see Tag fields),Title,URLs

alternate_json_dir = ""

def scene_from_json(scene_id):
    response = graphql.callGraphQL(
    """
    query FilenameBysceneId($id: ID){
      findScene(id: $id){
        files {
          path
        }
      }
    }""",
        {"id": scene_id},
    )
    log.debug(f"ID: {scene_id}")
    assert response is not None
    file = next(iter(response["findScene"]["files"]), None)
    if not file:
        log.debug(f"No files found for scene {scene_id}")
        return None

    file_path = Path(file["path"])
    log.debug(f"file_path: {file_path}")
    json_files = [file_path.with_suffix(suffix) for suffix in (".info.json", ".json",".mp4.json",".webm.json",".mkv.json")]
    thumbs_files = [file_path.with_suffix(suffix) for suffix in (".webp",".jpg",".jpeg")]
    
    if alternate_json_dir:
        json_files += [Path(alternate_json_dir) / p.name for p in json_files]

    json_file = next((f for f in json_files if f.exists()), None)

    if not json_file:
        paths = "', '".join(str(p) for p in json_files)
        log.debug(f"No JSON file found for '{file_path}': tried '{paths}'")
        return None

    scene = {}

    log.debug(f"Found JSON file: '{json_file}'")
    #log.debug(f"Found Image file: '{thumb_file}'")
    yt_json = json.loads(json_file.read_text(encoding="utf-8"))

    Sceneid = yt_json.get("id",)    

    if title := yt_json.get("title", yt_json.get("id")):
        scene["title"] = f"{title}- [{Sceneid}]"
        log.debug(f"title: '{title}'")

 
    url=[]
    #if post_shortcode := yt_json.get("post_shortcode"):
        #url.append(f"https://www.instagram.com/p/{post_shortcode}")
    if temp_url := yt_json.get("webpage_url"):
        url.append(temp_url)
    elif temp_url := yt_json.get("post_url"):
        url.append(temp_url)
    elif temp_url := yt_json.get("file_url"):
        url.append(temp_url)
    elif temp_url := yt_json.get("url"):
        url.append(temp_url)

    scene["urls"] = url

    #Studio is a WIP. Trying to make it more compatible with many sites.            
    #if studio := yt_json.get("category"):
        # scene["Studio"] = {"category": studio}
    #elif studio := yt_json.get("subcategory"):
        #scene["Studio"] = {"subcategory":studio}

    if casts := yt_json.get("username"):
        scene["performers"] = [{"name":casts}]
    elif casts := yt_json.get("tagged_username"):
        scene["performers"] =casts
    elif casts := yt_json.get("fullname"):
        scene["performers"] = [{"name":casts}]
    elif casts := yt_json.get("uploader"):
        scene["performers"] = [{"name":casts}]
    elif casts := yt_json.get("tagged_users"):
        scene["performers"] = casts
        
             
    tags = []
    tags = yt_json.get("tags", ["gallery_dl_yt_dlp_scrapped"])
    if category := yt_json.get("category"):
        tags.append(category)
    scene["tags"] = [{"name": tag} for tag in tags]

    if date_url := yt_json.get("date_url",):
        s = datetime.datetime.strptime(date_url, "%Y-%m-%d %H:%M:%S")
        scene["date"] = s.strftime("%Y-%m-%d")
    elif date_url := yt_json.get("date",):
        s = datetime.datetime.strptime(date_url, "%Y-%m-%d %H:%M:%S")
        scene["date"] = s.strftime("%Y-%m-%d")

    if details := yt_json.get("description"):
        scene["details"] = details
    elif details := yt_json.get("content"):
        scene["details"] = details

    return scene

if __name__ == "__main__":

    input = sys.stdin.read()
    input2 = codecs.encode(input, 'unicode-escape')
    input=re.sub(r'"title":.*?"url":', '"url":',input)
    #input = input.re.subplace("\\n","\\n").replace("\'", "\\'").replace("\"", '\\"').replace("\&", "\\&").replace("\r", "\\r").replace("\t", "\\t").replace("\b", "\\b").replace("\f", "\\f")
    log.debug(f"input: '{input}'")
    #log.debug(f"input2: '{input2}'")
    try:
        js = json.loads(input)
        scene_id = js["id"]
        ret = scene_from_json(scene_id)
        log.debug(json.dumps(ret))
        print(json.dumps(ret))
    except json.decoder.JSONDecodeError:
        scene = {}
        scene["tags"]=[{"name":"gallery_dl_yt_dlp_scrapped"}]
        print(json.dumps(scene))
        traceback.print_exc()
