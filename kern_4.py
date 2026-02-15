from modules.utils import load_config, show_boot_logo
from modules.ui.settings import kern_s
from modules._ui import kern_ui
import curses

def main(stdscr):
    config = load_config()
    if not config.get('setup_completed', False):
        kern_s.setup(stdscr, config)

    show_boot_logo(stdscr, config)

    tui = kern_ui(stdscr, config)
    tui.run()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()