import curses
import json
import time
from pathlib import Path

CONFIG_FILE = Path.home() / ".kern4_config.json"
TARGETS_FILE = Path.home() / ".kern4_stepper_targets.json"

# TODO: Add more themes (waiting for feedback)
DEFAULT_CONFIG = {
    "setup_completed": False,
    "fg_color": 7,
    "bg_color": 0,
    "logo_color": 2,
    "accent_color": 2,
    "error_color": 1,
    "theme": "dark_mode",
    "motor_mapping": [None, None, None, None],
    "window_layout": "default"
}

THEMES = {
    "dark_mode": {
        "name": "Minimalist",
        "description": "Gray, white & orange - minimalist and soo professional",
        "colors_256": {
            "primary": 101,
            "secondary": 102,
            "accent": 103,
            "highlight": 104,
            "border": 105,
            "warn": 106,
            "error": 107,
        },
        "colors_16": {
            "primary": 15,
            "secondary": 8,
            "accent": 7,
            "highlight": 3,
            "border": 8,
            "warn": 11,
            "error": 9,
        }
    },
    "monocrom": {
        "name": "Dark Mode",
        "description": "Minimalist white and gray contrast - it's just clean",
        "colors_256": {
            "primary": 111,
            "secondary": 112,
            "accent": 113,
            "highlight": 111,
            "border": 114,
            "warn": 113,
            "error": 111,
        },
        "colors_16": {
            "primary": 15,
            "secondary": 8,
            "accent": 7,
            "highlight": 15,
            "border": 8,
            "warn": 7,
            "error": 15,
        }
    },
    "amber": {
        "name": "Retro Amber",
        "description": "Classic amber - warm and kinda nostalgic I guess",
        "colors_256": {
            "primary": 121,
            "secondary": 122,
            "accent": 121,
            "highlight": 121,
            "border": 123,
            "warn": 121,
            "error": 127,
        },
        "colors_16": {
            "primary": 11,
            "secondary": 3,
            "accent": 11,
            "highlight": 11,
            "border": 3,
            "warn": 11,
            "error": 9,
        }
    },
    "sage": {
        "name": "Sage Green",
        "description": "Calm desaturated green - pretty zen and stable",
        "colors_256": {
            "primary": 131,
            "secondary": 134,
            "accent": 132,
            "highlight": 133,
            "border": 134,
            "warn": 136,
            "error": 137,
        },
        "colors_16": {
            "primary": 10,
            "secondary": 8,
            "accent": 2,
            "highlight": 10,
            "border": 8,
            "warn": 11,
            "error": 9,
        }
    },
    "lavender": {
        "name": "Soft Lavender",
        "description": "Mysterious pale purple - kinda elegant and modern",
        "colors_256": {
            "primary": 141,
            "secondary": 144,
            "accent": 142,
            "highlight": 143,
            "border": 144,
            "warn": 146,
            "error": 147,
        },
        "colors_16": {
            "primary": 13,
            "secondary": 8,
            "accent": 5,
            "highlight": 13,
            "border": 8,
            "warn": 11,
            "error": 9,
        }
    },
    "ochre": {
        "name": "Gray & Ochre",
        "description": "Minimalist earth tones - earthy and minimal",
        "colors_256": {
            "primary": 151,
            "secondary": 152,
            "accent": 153,
            "highlight": 154,
            "border": 152,
            "warn": 156,
            "error": 157,
        },
        "colors_16": {
            "primary": 7,
            "secondary": 8,
            "accent": 3,
            "highlight": 11,
            "border": 8,
            "warn": 11,
            "error": 9,
        }
    },
    "nasa": {
        "name": "NASA Style",
        "description": "Classic NASA mission control - it looks official", # Not yet!
        "colors_256": {
            "primary": 161,
            "secondary": 162,
            "accent": 163,
            "highlight": 164,
            "border": 165,
            "warn": 166,
            "error": 167,
        },
        "colors_16": {
            "primary": 15,
            "secondary": 4,
            "accent": 6,
            "highlight": 14,
            "border": 12,
            "warn": 11,
            "error": 9,
        }
    },
    # Fun fact, this theme is inspired after the settlement from the project Aletheia (National Space Society)
    "aletheia": {
        "name": "Aletheia",
        "description": "White, red, blue and gray theme - gives off space vibes",
        "colors_256": {
            "primary": 171,
            "secondary": 172,
            "accent": 173,
            "highlight": 174,
            "border": 175,
            "warn": 176,
            "error": 177,
        },
        "colors_16": {
            "primary": 15,
            "secondary": 8,
            "accent": 12,
            "highlight": 9,
            "border": 7,
            "warn": 11,
            "error": 9,
        }
    }
}

# Generated using this website: https://www.asciiart.eu/image-to-ascii
BOOT_LOGO = """
████                                                                                    ████         ████████████████   
████                                                                                    ████        ███████████████████ 
████     ███         ████         ███████     ████████                              ████████       █████████████████████
████    ████         ████        █████████    ████████                             █████████       █████████████████████
████    ████         ████        ████████▓    ████████                             █████████       █████████████████████
████████         ████████████    ████         ████    ████    █████████████    ████     ████       █████████████████████
████████         ████████████    ████         ████    ████    █████████████    ████     ████       █████████████████████
████    ████     ████            ████         ████    ████                     █████████████       █████████████████████
████    ████     ████            ████         ████    ████                     █████████████       █████████████████████
████    ████         ████████    ████         ████    ████                              ████       ████████████████████ 
████    ████         ████████    ████         ████    ████                              ████         ████████████████
"""

COLOR_NAMES = [
    "Black", "Red", "Green", "Yellow", 
    "Blue", "Magenta", "Cyan", "White",
    "Bright Black", "Bright Red", "Bright Green", "Bright Yellow",
    "Bright Blue", "Bright Magenta", "Bright Cyan", "Bright White"
]

# will add more...
def init_color_256():
    if curses.COLORS < 256:
        return False
    
    try:
        curses.init_pair(101, 255, 0)
        curses.init_pair(102, 244, 0)
        curses.init_pair(103, 208, 0)
        curses.init_pair(104, 214, 0)
        curses.init_pair(105, 240, 0)
        curses.init_pair(106, 226, 0)
        curses.init_pair(107, 196, 0)
        
        curses.init_pair(111, 255, 0)
        curses.init_pair(112, 250, 0)
        curses.init_pair(113, 244, 0)
        curses.init_pair(114, 238, 0)
        curses.init_pair(115, 232, 0)
        
        curses.init_pair(121, 214, 0)
        curses.init_pair(122, 208, 0)
        curses.init_pair(123, 172, 0)
        curses.init_pair(124, 130, 0)
        curses.init_pair(127, 196, 0)
        
        curses.init_pair(131, 108, 0)
        curses.init_pair(132, 65, 0)
        curses.init_pair(133, 71, 0)
        curses.init_pair(134, 244, 0)
        curses.init_pair(136, 226, 0)
        curses.init_pair(137, 196, 0)
        
        curses.init_pair(141, 183, 0)
        curses.init_pair(142, 147, 0)
        curses.init_pair(143, 189, 0)
        curses.init_pair(144, 244, 0)
        curses.init_pair(146, 226, 0)
        curses.init_pair(147, 196, 0)
        
        curses.init_pair(151, 250, 0)
        curses.init_pair(152, 244, 0)
        curses.init_pair(153, 178, 0)
        curses.init_pair(154, 220, 0)
        curses.init_pair(156, 226, 0)
        curses.init_pair(157, 196, 0)
        
        curses.init_pair(161, 255, 0)
        curses.init_pair(162, 33, 0)
        curses.init_pair(163, 51, 0)
        curses.init_pair(164, 39, 0)
        curses.init_pair(165, 27, 0)
        curses.init_pair(166, 226, 0)
        curses.init_pair(167, 196, 0)
        
        curses.init_pair(171, 255, 0)
        curses.init_pair(172, 244, 0)
        curses.init_pair(173, 33, 0)
        curses.init_pair(174, 196, 0)
        curses.init_pair(175, 250, 0)
        curses.init_pair(176, 226, 0)
        curses.init_pair(177, 196, 0)
        
        curses.init_pair(200, 16, 255)
        
        return True
    except:
        return False

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        pass

def load_targets():
    if TARGETS_FILE.exists():
        try:
            with open(TARGETS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_targets(targets):
    try:
        with open(TARGETS_FILE, 'w') as f:
            json.dump(targets, f, indent=2)
    except:
        pass

def show_boot_logo(stdscr, config):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    logo_lines = BOOT_LOGO.strip().split('\n')
    logo_height = len(logo_lines)
    logo_width = max(len(line) for line in logo_lines)
    
    start_y = max(0, (h - logo_height) // 2)
    start_x = max(0, (w - logo_width) // 2)
    
    try:
        logo_color = config.get('logo_color', 2)
        curses.init_pair(10, logo_color, config.get('bg_color', 0))
        color = curses.color_pair(10) | curses.A_BOLD
    except:
        color = curses.A_BOLD
    
    for i, line in enumerate(logo_lines):
        if start_y + i < h - 1:
            try:
                stdscr.addstr(start_y + i, start_x, line[:w-start_x-1], color)
            except:
                pass
    
    loading_msg = "Loading modules..." # TODO: add a dynamic loading message...
    if start_y + logo_height + 2 < h:
        try:
            stdscr.addstr(start_y + logo_height + 2, 
                         max(0, (w - len(loading_msg)) // 2), 
                         loading_msg, color)
        except:
            pass
    
    stdscr.refresh()
    time.sleep(2.5)