import random

import flask
import src.config

metadataBP = flask.Blueprint("metadata", __name__, url_prefix="/api/v1/metadata")


@metadataBP.route("/")
async def metadataFunction():
    a = flask.request.args.get("a")  # AUTH
    c = flask.request.args.get("c")  # CATEGORY
    g = flask.request.args.get("g")  # GENRE
    id = flask.request.args.get("id")  # ID
    q = flask.request.args.get("q")  # QUERY
    r = flask.request.args.get("r")  # RANGE
    s = flask.request.args.get("s")  # SORT-ORDER
    config = src.config.readConfig()
    tmp_metadata = src.metadata.readMetadata(config)

    if (
        any(a == account["auth"] for account in config["account_list"])
        or config.get("auth") == False
    ):
        account = next((i for i in config["account_list"] if i["auth"] == a), None)
        whitelisted_categories_metadata = []
        for category in tmp_metadata:
            category_config = next(
                (i for i in config["category_list"] if i["id"] == category["id"]), None
            )
            if category_config:
                if category_config.get("whitelist"):
                    if account["auth"] in category_config.get("whitelist"):
                        whitelisted_categories_metadata.append(category)
                else:
                    whitelisted_categories_metadata.append(category)
            else:
                whitelisted_categories_metadata.append(category)
        tmp_metadata = whitelisted_categories_metadata
        whitelisted_accounts_metadata = []
        if account:
            if account.get("whitelist"):
                for x in tmp_metadata:
                    if any(x["id"] == whitelist for whitelist in account["whitelist"]):
                        whitelisted_accounts_metadata.append(x)
                tmp_metadata = whitelisted_accounts_metadata
        if c:
            tmp_metadata = [
                next((i for i in tmp_metadata if i["categoryInfo"]["name"] == c), None)
            ]
            if tmp_metadata:
                pass
            else:
                return (
                    flask.jsonify(
                        {
                            "code": 400,
                            "content": None,
                            "message": "The category provided could not be found.",
                            "success": False,
                        }
                    ),
                    400,
                )
        if g:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = [
                    item for item in category["children"] if g in item["genres"]
                ]
                index += 1
        if q:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = [
                    item
                    for item in category["children"]
                    if q.lower() in item["title"].lower()
                ]
                index += 1
        if s:
            index = 0
            for category in tmp_metadata:
                if s == "alphabet-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: k["title"]
                        )
                    except:
                        pass
                elif s == "alphabet-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: k["title"], reverse=True
                        )
                    except:
                        pass
                elif s == "date-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: tuple(map(int, k["releaseDate"].split("-"))),
                        )
                    except:
                        pass
                elif s == "date-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: tuple(map(int, k["releaseDate"].split("-"))),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "popularity-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: float(k["popularity"])
                        )
                    except:
                        pass
                elif s == "popularity-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: float(k["popularity"]),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "vote-asc":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"], key=lambda k: float(k["voteAverage"])
                        )
                    except:
                        pass
                elif s == "vote-des":
                    try:
                        tmp_metadata[index]["children"] = sorted(
                            category["children"],
                            key=lambda k: float(k["voteAverage"]),
                            reverse=True,
                        )
                    except:
                        pass
                elif s == "random":
                    try:
                        random.shuffle(tmp_metadata[index]["children"])
                    except:
                        pass
                else:
                    return (
                        flask.jsonify(
                            {
                                "code": 400,
                                "content": None,
                                "message": "Bad request! Sorting parameter '%s' does not exist."
                                % (s),
                                "success": False,
                            }
                        ),
                        400,
                    )
                index += 1
        for x in tmp_metadata:
            x["length"] = len(x["children"])
        if id:
            tmp_metadata = src.metadata.jsonExtract(tmp_metadata, "id", id, False)
            config, drive = src.credentials.refreshCredentials(config)
            if tmp_metadata:
                if config.get("build_type") == "full":
                    pass
                else:
                    tmp_metadata["children"] = []
                    if (
                        tmp_metadata.get("title")
                        and tmp_metadata.get("type") == "directory"
                    ):
                        for item in src.drivetools.driveIter(
                            tmp_metadata, drive, "video"
                        ):
                            if item["mimeType"] == "application/vnd.google-apps.folder":
                                item["type"] = "directory"
                                tmp_metadata["children"].append(item)
                            else:
                                item["type"] = "file"
                                tmp_metadata["children"].append(item)
                return (
                    flask.jsonify(
                        {
                            "code": 200,
                            "content": tmp_metadata,
                            "message": "Metadata parsed successfully.",
                            "success": True,
                        }
                    ),
                    200,
                )
            tmp_metadata = (
                drive.files().get(fileId=id, supportsAllDrives=True).execute()
            )
            if tmp_metadata["mimeType"] == "application/vnd.google-apps.folder":
                tmp_metadata["type"] = "directory"
                tmp_metadata["children"] = []
                for item in src.drivetools.driveIter(tmp_metadata, drive, "video"):
                    if (
                        tmp_metadata.get("mimeType")
                        == "application/vnd.google-apps.folder"
                    ):
                        tmp_metadata["type"] = "directory"
                        tmp_metadata["children"].append(item)
                    else:
                        tmp_metadata["type"] = "file"
                        tmp_metadata["children"].append(item)
        if r:
            index = 0
            for category in tmp_metadata:
                tmp_metadata[index]["children"] = eval(
                    "category['children']" + "[" + r + "]"
                )
                index += 1
        return (
            flask.jsonify(
                {
                    "code": 200,
                    "content": tmp_metadata,
                    "message": "Metadata parsed successfully.",
                    "success": True,
                }
            ),
            200,
        )
    else:
        return (
            flask.jsonify(
                {
                    "code": 401,
                    "content": None,
                    "message": "Your credentials are invalid.",
                    "success": False,
                }
            ),
            401,
        )
