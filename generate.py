#!/usr/bin/env python3
"""Generate DM42 skin configuration files for Free42."""

import json
import os
import sys
from functools import partial

from PIL import Image

# Original size in pixels of the HP42
ORIG_HP42_WIDTH = 131
ORIG_HP42_HEIGHT = 16

# File containing the layout data
LAYOUT_FILENAME = "dm42.json"

# The skin of the DM42
SKIN_FILENAME = "dm42.png"
SKIN_WIDTH = 2903
SKIN_HEIGHT = 5462
SKIN_ACTIVE_SHIFT = 5700

# The size, position and colors of the display in the original GIF
DISPLAY_WIDTH = 2206
DISPLAY_LEFT = 350
DISPLAY_BOTTOM = 1713
DISPLAY_FOREGROUND = "2c302e"
DISPLAY_BACKGROUND = "caccc9"


# --------------------------------------------------------------------------- #
# CREATE SKIN FILES                                                           #
# --------------------------------------------------------------------------- #


def resize_image(mx, my, filename):
    """Resize the skin image to fit the given x and y magnification."""
    coef = compute_coef(mx, my)
    img = Image.open(SKIN_FILENAME)
    size = [scale(v, coef) for v in img.size]
    img.resize(size).save(filename, "GIF", optimize=True)


def generate_layout(mx, my, filename):
    """Generate the layout file with given x and y magnification."""
    # Compute the scaling coefficient
    coef = compute_coef(mx, my)
    # Load the layout data
    with open(LAYOUT_FILENAME, "r") as f:
        data = json.load(f)
    # Generate the layout file
    with open(filename, "w") as f:
        write = partial(print, file=f)
        write(gen_headers(mx, my, data))
        write()
        write(gen_skin(coef))
        write(gen_display(mx, my, coef))
        write()
        write(gen_keys(data, coef))
        write()
        write(gen_macros(data))
        write()
        write(gen_annunciators(data, coef))
        write()


# --------------------------------------------------------------------------- #
# GENERATE LAYOUT PARTS                                                       #
# --------------------------------------------------------------------------- #


def gen_headers(mx, my, data):
    """Generate the headers of the layout file."""
    lines = [
        "# DM42 skin for the Free42 simulator",
        "# By Fabien Dubosson <fabien.dubosson@gmail.com>",
        "# https://github.com/StreakyCobra/dm42-skin",
        "# Version: " + data["version"] + f", magnifications: {mx} {my}",
    ]
    return "\n".join(lines)


def gen_skin(coef):
    """Generate the «Skin» line of the layout file."""
    skin = [scale(v, coef, as_str=True) for v in [0, 0, SKIN_WIDTH, SKIN_HEIGHT]]
    return f"Skin: {','.join(skin)}"


def gen_display(mx, my, coef):
    """Generate the «Display» line of the layout file."""
    left = scale(DISPLAY_LEFT, coef)
    top = round(DISPLAY_BOTTOM * coef - ORIG_HP42_HEIGHT * my)
    return (
        f"Display: {left},{top} {mx} {my} " f"{DISPLAY_BACKGROUND} {DISPLAY_FOREGROUND}"
    )


def gen_keys(data, coef):
    """Generate the «Key» lines of the layout file."""
    keys = data.get("keys", {})
    keys = {i: expend_key_data(v) for i, v in keys.items()}
    keys = {i: scale(v, coef, as_str=True) for i, v in keys.items()}
    keys = [
        f"Key: {i} "
        + ",".join(k["sensitivity"])
        + " "
        + ",".join(k["display"])
        + " "
        + ",".join(k["active"])
        for i, k in keys.items()
    ]
    return "\n".join(keys)


def gen_macros(data):
    """Generate the «Macro» lines of the layout file."""
    macros = data.get("macros", {})
    macros = [f"Macro: {i} " + " ".join(as_str(m)) for i, m in macros.items()]
    return "\n".join(macros)


def gen_annunciators(data, coef):
    """Generate the «Annunciator» lines of the layout file."""
    annunciators = data.get("annunciators", {})
    annunciators = {i: scale(v, coef, as_str=True) for i, v in annunciators.items()}
    annunciators = [
        f"Annunciator: {i} " + ",".join(k["rectangle"]) + " " + ",".join(k["active"])
        for i, k in annunciators.items()
    ]
    return "\n".join(annunciators)


# --------------------------------------------------------------------------- #
# HELPERS                                                                     #
# --------------------------------------------------------------------------- #


def scale(obj, coef, as_str=False):
    """Scale an object recursively with the given coefficient."""
    f = str if as_str else int
    if hasattr(obj, "items"):
        return {k: scale(v, coef, as_str) for k, v in obj.items()}
    try:
        return [scale(v, coef, as_str) for v in obj]
    except TypeError:
        return f(round(obj * coef))


def as_str(obj):
    """Return an object as string recursively."""
    if hasattr(obj, "items"):
        return {k: as_str(v) for k, v in obj.items()}
    if type(obj) == str:
        return '"' + obj + '"'
    try:
        return [as_str(v) for v in obj]
    except TypeError:
        return str(obj)


def compute_coef(mx, my):
    """Compute the scaling coefficient from the given x and y magnification."""
    return (mx * ORIG_HP42_WIDTH) / DISPLAY_WIDTH


def expend_key_data(key):
    """Expend key data in case of missing information."""
    if "display" not in key:
        key["display"] = key["sensitivity"]
    if "active" not in key:
        key["active"] = [
            key["sensitivity"][0],
            SKIN_ACTIVE_SHIFT + key["sensitivity"][1],
        ]
    return key


# --------------------------------------------------------------------------- #
# RUNNING SCRIPT                                                              #
# --------------------------------------------------------------------------- #


def main():
    """Run the script."""

    # Handle help flag
    if "-h" in sys.argv:
        usage(sys.argv[0])

    # Get arguments
    if len(sys.argv) > 1:
        mx = int(sys.argv[1])  # x magnification
    else:
        mx = 1
    if len(sys.argv) > 2:
        my = int(sys.argv[2])  # y magnification
    else:
        my = mx * 2
    if len(sys.argv) > 3:
        name = sys.argv[3]  # Name of the skin
    else:
        name = f"dm42_{mx}"

    # Ensure the output directory exits
    folder = os.path.join("skins", name)
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Resize the skin image
    resize_image(mx, my, os.path.join(folder, f"{name}.gif"))

    # Generate the associated skin layout
    generate_layout(mx, my, os.path.join(folder, f"{name}.layout"))


def usage(program):
    print("Usage:\n")
    print(f"\t{program} [<x_magnification>] [<y_magnification>] [<skin_name>]\n")
    print(f"Examples:\n")
    print(f"\t{program} 2")
    print(f"\t{program} 2 5")
    print(f"\t{program} 2 5 'dm42-custom'")
    sys.exit(1)


if __name__ == "__main__":
    main()
