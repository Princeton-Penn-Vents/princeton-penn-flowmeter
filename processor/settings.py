#!/usr/bin/env python3

from processor.setting import IncrSetting, SelectionSetting, Setting
from processor.display_settings import FilenameSetting, CurrentSetting, ResetSetting
from processor.config import config

from typing import Dict
from confuse import ConfigView
from pprint import pprint


def get_setting(c: ConfigView) -> Setting:
    type_name = c["type"].get()
    if type_name == "Incr":
        return IncrSetting(
            default=c["default"].as_number(),
            min=c["min"].as_number(),
            max=c["max"].as_number(),
            incr=c["incr"].as_number(),
            name=c["name"].get(),
            unit=c["unit"].get() if "unit" in c else None,
            lcd_name=c["lcd_name"].get() if "lcd_name" in c else None,
        )
    elif type_name == "Selection":
        return SelectionSetting(
            default=c["default"].get(int),
            listing=[v.as_number() for v in c["items"]],
            name=c["name"].get(),
            lcd_name=c["lcd_name"].get() if "lcd_name" in c else None,
        )
    elif type_name == "Current":
        return CurrentSetting(
            default=c["default"].get(int),
            listing=[v.as_number() for v in c["items"]],
            name="Current:",
        )
    elif type_name == "Reset":
        return ResetSetting(name=c["name"].get(),)
    elif type_name == "Filename":
        return FilenameSetting("Log filename")
    else:
        raise RuntimeError(
            f"Invalid type {type_name!r}, needs to be defined in setting.py/settings.py"
        )


def get_live_settings() -> Dict[str, Setting]:
    "Get the live version of the configuration dictionary"

    d: Dict[str, Setting] = {}
    all_settings = [config["rotary-live"], config["rotary"]]
    for settings in all_settings:
        for setting in settings:
            d[setting] = get_setting(settings[setting])
    return d


def get_remote_settings() -> Dict[str, Setting]:
    "Get the non-live version of the configuration dictionary"
    d: Dict[str, Setting] = {}
    all_settings = [config["rotary"]]
    for settings in all_settings:
        for setting in settings:
            d[setting] = get_setting(settings[setting])
    return d


if __name__ == "__main__":
    print("Live ----/n")
    pprint(get_live_settings())
    print("/nRemote ----/n")
    pprint(get_remote_settings())
