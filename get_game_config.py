import json
import os
import jsonpatch
import time
import datetime

from bundle import MODS_DIR, CONFIG_DIR, CONFIG_PATCH_DIR

__game_config = json.load(open(os.path.join(CONFIG_DIR, "main.json"), 'r', encoding='utf-8'))

def remove_duplicate_items():
    indexes = {}
    items = __game_config["items"]
    num_duplicate = 0

    while True:
        index = 0
        duplicate = False
        for item in items:
            if item["id"] in indexes:
                del items[indexes[item["id"]]]
                indexes.clear()
                duplicate = True
                num_duplicate += 1
                break

            indexes[item["id"]] = index
            index += 1

        if duplicate:
            continue

        print(f" * Removed {num_duplicate} duplicate items.")
        break

def apply_config_patch(filename):
    patch = json.load(open(filename, 'r'))
    jsonpatch.apply_patch(__game_config, patch, in_place=True)

def patch_game_config():

    if os.path.exists(os.path.join(CONFIG_PATCH_DIR, "patches.txt")):
        with open(os.path.join(CONFIG_PATCH_DIR, "patches.txt"), "r") as f:
            lines = f.readlines()
            f.close()

        for line in lines:
            patch = line.strip()
            if patch.startswith("#"):
                continue
            if patch != "":
                patch = patch.replace(".json", "")
                patch_path = f"{CONFIG_PATCH_DIR}/{patch}.json"
                if os.path.exists(patch_path):
                    apply_config_patch(patch_path)
                    print(" * Patch applied:", patch)
                else:
                    print(" * Patch ERROR: Could not find", patch)

def modify_game_config():

    if os.path.exists(os.path.join(MODS_DIR, "mods.txt")):
        with open(os.path.join(MODS_DIR, "mods.txt"), "r") as f:
            lines = f.readlines()
            f.close()

        for line in lines:
            mod = line.strip()
            if mod.startswith("#"):
                continue
            if mod != "":
                mod = mod.replace(".json", "")
                mod_path = f"{MODS_DIR}/{mod}.json"
                if os.path.exists(mod_path):
                    apply_config_patch(mod_path)
                    print(" * Mod applied:", mod)
                else:
                    print(" * Mod ERROR: Could not find", mod)

print (" [+] Applying config patches...")
patch_game_config()

print (" [+] Applying config mods...")
modify_game_config()

print (" [+] Cleaning config duplicates...")
remove_duplicate_items()

def get_game_config() -> dict:
    make_dynamic(__game_config)
    return __game_config

def game_config() -> dict:
    return get_game_config()

##########
# PLAYER #
##########

def get_xp_from_level(level: int) -> int:
    return __game_config["levels"][int(level)]["exp_required"]

def get_level_from_xp(xp: int) -> int:
    i = 0
    for lvl in __game_config["levels"]:
        if lvl["exp_required"] > int(xp):
            return i
        i += 1
    return 0

#########
# ITEMS #
#########

# ID

items_dict_id_to_items_index = {int(item["id"]): i for i, item in enumerate(__game_config["items"])}

def get_item_from_id(id: int) -> dict:
    items_index = items_dict_id_to_items_index[int(id)] if int(id) in items_dict_id_to_items_index else None
    return __game_config["items"][items_index] if items_index is not None else None

def get_attribute_from_item_id(id: int, attribute_name: str) -> str:
    item = get_item_from_id(id)
    return item[attribute_name] if item and attribute_name in item else None

def get_name_from_item_id(id: int) -> str:
    return get_attribute_from_item_id(id, "name")

# subcat_functional

items_dict_subcat_functional_to_items_index = {int(item["subcat_functional"]): i for i, item in enumerate(__game_config["items"])}

def get_item_from_subcat_functional(subcat_functional: int) -> dict:
    items_index = items_dict_subcat_functional_to_items_index[int(subcat_functional)] if int(subcat_functional) in items_dict_subcat_functional_to_items_index else None
    return __game_config["items"][items_index] if items_index is not None else None

#########
# GOALS #
#########

goals_id_to_goals_index = {int(item["id"]): i for i, item in enumerate(__game_config["goals"])}

def get_goal_from_id(id: int) -> dict:
    items_index = goals_id_to_goals_index[int(id)] if int(id) in goals_id_to_goals_index else None
    return __game_config["goals"][items_index] if items_index is not None else None

def get_attribute_from_goal_id(id: int, attribute_name: str) -> str:
    goal = get_goal_from_id(id)
    return goal[attribute_name] if goal and attribute_name in goal else None

###################
# INVENTORY ITEMS #
###################

def get_inventory_item_name(item: int):
    itemstr = str(item)
    items = __game_config["inventory_items"]
    if itemstr in items:
        return items[itemstr]["name"]
    return None

def get_collection_name(collection: int):
    index = max(0, collection - 1)
    collections = __game_config["collections"]
    if index < len(collections):
        return collections[index]["name"]
    return None

def get_collection_prize(collection: int):
    index = max(0, collection - 1)
    collections = __game_config["collections"]
    if index < len(collections):
        return json.loads(collections[index]["prize"])
    return None

###################
# PREMIUM ACCOUNT #
###################

def get_premium_days(package_index: int):
    packages = __game_config["globals"]["PREMIUM_ACCOUNTS"]
    index = package_index
    if index >= len(packages):
        index = len(packages) - 1
    package = packages[index]
    if "time" in package:
        return package["time"]
    return 0

################################
# WEEKLY REWARD (MONDAY BONUS) #
################################

def get_weekly_reward_length() -> int:
    # This would be better if it was called at the start, instead of being calculated every time
    rewards = __game_config["globals"]["MONDAY_BONUS_REWARDS"]
    length = 1
    for reward in rewards:
        value = reward["value"]
        if type(value) == list:
            length = max(length, len(value))

    return length

#######################
# MAKE CONFIG DYNAMIC #
#######################

def timestamp_now():
    return int(time.time())

def make_dynamic(config):
    # darts
    if "darts_items" in config:
        darts_items = config["darts_items"]

        # grab first timestamp in config
        ts_now = timestamp_now()
        ts_first = 0
        week_length = 604800
        num_items = len(darts_items)
        
        for game in darts_items:
            ts_first = time.mktime(datetime.datetime.strptime(game["start_date"], "%Y-%m-%d %H:%M:%S").timetuple())
            break

        # 30 items are in config, first 4 are invalid for SW s
        # so since we load the patch that removes the first 4 items there are 26 + 1
        # the 27th is a copy of the first one to fix wrapping on last one
        wrap_seconds = week_length * num_items
        if num_items >= 26:
            wrap_seconds -= week_length

        # should the dates be updated?
        if ts_now - ts_first >= wrap_seconds:
            weeks_passed = (ts_now - ts_first) / week_length
            shift_times = int(weeks_passed // num_items)
            seconds = wrap_seconds * shift_times

            # we need to fix start dates to mondays since darts reset every monday regardless of start dates
            new_date = datetime.datetime.fromtimestamp(ts_first + seconds)
            seconds -= (new_date.isoweekday() - 1) * 86400
            new_date = datetime.datetime.fromtimestamp(ts_first + seconds)
            new_date_str = new_date.strftime("%Y-%m-%d %H:%M:%S")
            weekday = new_date.isoweekday()

            update_darts(darts_items, ts_first, seconds, 0)    # the number here is the debug level
            print("[CONFIG] Darts minigame is now dynamic again!")

# updates darts start dates
def update_darts(darts_items, ts_first, seconds, debug = 0):
    week_length = 604800
    shift = seconds
    for game in darts_items:
        # we ignore the date in config and just rebuild dates based on first date in config starting on monday
        ts = time.mktime(datetime.datetime.strptime(game["start_date"], "%Y-%m-%d %H:%M:%S").timetuple())
        new_date = datetime.datetime.fromtimestamp(ts_first + shift)

        # account for daylight savings
        if new_date.hour == 23:
            shift += 3600
            new_date = datetime.datetime.fromtimestamp(ts_first + shift)
        elif new_date.hour == 1:
            shift -= 3600
            new_date = datetime.datetime.fromtimestamp(ts_first + shift)
            
        # fix to monday
        weekday = new_date.isoweekday()
        if weekday == 2:
            shift -= 86400
            new_date = datetime.datetime.fromtimestamp(ts_first + shift)
        elif weekday == 7:
            shift += 86400
            new_date = datetime.datetime.fromtimestamp(ts_first + shift)

        weekday = new_date.isoweekday()
        new_date = new_date.strftime("%Y-%m-%d %H:%M:%S")
        if debug >= 1:
            test = game["start_date"]
            
            # output minor prizes
            if debug >= 2:
                game_id = game["id"]
                print(f"Darts minigame ID: {game_id}")

                idx = 1
                for unit in game["items"]:
                    item_id = int(unit)
                    item = get_item_from_id(item_id)
                    if item:
                        item_name = item["name"]
                    else:
                        item_name = "INVALID UNIT"

                    print(f"[DEBUG] Minor Prize {idx} = ({item_id}) {item_name}")
                    idx += 1

            # output major prize and date change
            major_prize = int(game["extra_item"])
            item = get_item_from_id(major_prize)
            item_name = "INVALID MAJOR PRIZE"
            if item:
                item_name = item["name"]

            print(f"[DEBUG] {test} -> {new_date} (weekday = {weekday}) -> ({major_prize}) {item_name}")

        game["start_date"] = new_date

        # make sure each one lasts exactly 7 days from first one
        shift += week_length