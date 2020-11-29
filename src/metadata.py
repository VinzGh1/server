import json
import os
import re
import time

import requests

from src.walk import driveWalk


def parseName(name):
    match_1 = re.search(
        r'''^\(([1-2][0-9]{3})\)([^\.]*)''', name)  # Example: (2008) Iron Man.mkv
    match_2 = re.search(
        r'''^([^\.]{1,}?)\(([1-2][0-9]{3})\)''', name)  # Example: Iron Man (2008).mkv
    match_3 = re.search(r'''^([^\*]{1,}?)([1-2][0-9]{3})[^\*]''',
                        name)  # Example: Iron.Man.2008.REMASTERED.1080p.BluRay.x265-RARBG.mkv
    if match_1:
        try:
            title = match_1.group(2)
            year = match_1.group(1)
            return title, year
        except:
            pass
    elif match_2:
        try:
            title = match_2.group(1)[:-1]
            year = match_2.group(2)
            return title, year
        except:
            pass
    elif match_3:
        try:
            if match_3.group(1) != "(":
                title = match_3.group(1).replace(".", " ")[:-1]
                year = match_3.group(2)
                return title, year
        except:
            pass


def mediaIdentifier(tmdb_api_key, title, year, backdrop_base_url, poster_base_url, movie=False, tv=False):
    if movie:
        search_url = "http://api.themoviedb.org/3/search/movie?api_key=" + \
            tmdb_api_key+"&query=" + title + "&year=" + year
        search_content = json.loads((requests.get(search_url)).content)
        try:
            title = search_content["results"][0]["title"]
            posterPath = poster_base_url + \
                search_content["results"][0]["poster_path"]
            backdropPath = backdrop_base_url + \
                search_content["results"][0]["backdrop_path"]
            releaseDate = search_content["results"][0]["release_date"]
            overview = search_content["results"][0]["overview"]
        except:
            posterPath = ""
            backdropPath = ""
            releaseDate = year + "-01-01"
            overview = ""
        return title, posterPath, backdropPath, releaseDate, overview
    elif tv:
        search_url = "http://api.themoviedb.org/3/search/tv?api_key=" + \
            tmdb_api_key+"&query=" + title + "&year=" + year
        search_content = json.loads((requests.get(search_url)).content)
        try:
            title = search_content["results"][0]["name"]
            posterPath = poster_base_url + \
                search_content["results"][0]["poster_path"]
            backdropPath = backdrop_base_url + \
                search_content["results"][0]["backdrop_path"]
            releaseDate = search_content["results"][0]["first_air_date"]
            overview = search_content["results"][0]["overview"]
        except:
            posterPath = ""
            backdropPath = ""
            releaseDate = year + "-01-01"
            overview = ""
        return title, posterPath, backdropPath, releaseDate, overview


def writeMetadata(category_list, drive, tmdb_api_key, backdrop_base_url, poster_base_url):
    placeholder_metadata = []
    for category in category_list:
        index = next((i for i, item in enumerate(category_list) if (
            item["name"] == category["name"]) and (item["id"] == category["id"])), None)
        if category["type"] == "movies":
            tmp_metadata = []
            for path, root, dirs, files in driveWalk(category["id"], False, drive):
                for file in files:
                    if "video" in file["mimeType"]:
                        try:
                            title, year = parseName(
                                file["name"])
                            file["title"], file["posterPath"], file["backdropPath"], file["releaseDate"], file["overview"] = mediaIdentifier(
                                tmdb_api_key, title, year, backdrop_base_url, poster_base_url, True, False)
                        except:
                            file["title"], file["posterPath"], file["backdropPath"], file["releaseDate"], file["overview"] = file["name"][:-len(
                                file["fullFileExtention"])], "", "", "1900-01-01", ""
                root["files"] = files
                root["folders"] = dirs
                stdin = "tmp_metadata"
                for l in range(len(path)-2):
                    stdin = stdin + "[-1]['folders']"
                eval(stdin+".append(root)")
            placeholder_metadata.append({"name": category["name"], "type": category["type"],
                                         "id": category["id"], "driveId": category["driveId"], "files": tmp_metadata[0]["files"], "folders": tmp_metadata[0]["folders"]})
        elif category["type"] == "tv":
            tmp_metadata = []
            for path, root, dirs, files in driveWalk(category["id"], False, drive):
                root["files"] = [
                    file for file in files if "video" in file["mimeType"]]
                for dir in dirs:
                    try:
                        title, year = parseName(
                            dir["name"])
                        dir["title"], dir["posterPath"], dir["backdropPath"], dir["releaseDate"], dir["overview"] = mediaIdentifier(
                            tmdb_api_key, title, year, backdrop_base_url, poster_base_url, False, True)
                    except:
                        dir["title"], dir["posterPath"], dir["backdropPath"], dir["releaseDate"], dir["overview"] = dir["name"], "", "", "1900-01-01", ""
                root["folders"] = dirs
                stdin = "tmp_metadata"
                for l in range(len(path)-2):
                    stdin = stdin + "[-1]['folders']"
                eval(stdin+".append(root)")
            placeholder_metadata.append({"name": category["name"], "type": category["type"],
                                         "id": category["id"], "driveId": category["driveId"], "files": tmp_metadata[0]["files"], "folders": tmp_metadata[0]["folders"]})

    metadata = placeholder_metadata

    if os.path.exists("./metadata"):
        pass
    else:
        os.mkdir("./metadata")
    with open("./metadata/"+time.strftime("%Y%m%d-%H%M%S")+".json", "w+") as w:
        w.write(json.dumps(metadata))

    return metadata