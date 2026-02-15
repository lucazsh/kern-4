import curses

def handler(self, key):
    if key == -1:
        return
    
    if key in (ord('q'), ord('Q')):
        self.quit_app()
        return
    
    if key == curses.KEY_UP:
        self.selected_menu_idx = max(0, self.selected_menu_idx - 1)
        if self.selected_menu_idx < self.menu_scroll:
            self.menu_scroll = self.selected_menu_idx
    elif key == curses.KEY_DOWN:
        self.selected_menu_idx = min(len(self.menu_items) - 1, self.selected_menu_idx + 1)
        h, w = self.stdscr.getmaxyx()
        visible_items = (h - 6)
        if self.selected_menu_idx >= self.menu_scroll + visible_items:
            self.menu_scroll = self.selected_menu_idx - visible_items + 1
    
    elif key in (ord('\n'), ord('\r'), curses.KEY_ENTER, 10, 13):
        if 0 <= self.selected_menu_idx < len(self.menu_items):
            _, _, func = self.menu_items[self.selected_menu_idx]
            func()
    
    elif key in range(ord('0'), ord('9') + 1):
        num = chr(key)
        for i, (k, _, func) in enumerate(self.menu_items):
            if k == num:
                self.selected_menu_idx = i
                func()
                break