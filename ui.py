from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, Label, ListView, ListItem, Select
from textual.containers import Container, Horizontal
from db import get_folders_and_bookmarks, add_bookmark
from utils import fetch_title
from textual import events
from textual.reactive import reactive
import random
import webbrowser

class BookmarkApp(App):
    CSS_PATH = "app.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "add", "Add Bookmark"),
        ("e", "edit", "Edit Bookmark"),
        ("delete", "delete", "Delete Bookmark"),
        ("left", "left", "Left"),
        ("right", "right", "Right"),
        ("up", "up", "Up"),
        ("down", "down", "Down"),
        ("enter", "enter", "Select"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(r'''
 __         __     __   __     __  __     _____     ______    
/\ \       /\ \   /\ "-.\ \   /\ \/ /    /\  __-.  /\  == \   
\ \ \____  \ \ \  \ \ \-.  \  \ \  _"-.  \ \ \/\ \ \ \  __<   
 \ \_____\  \ \_\  \ \_\\"\_\  \ \_\ \_\  \ \____-  \ \_____\ 
  \/_____/   \/_/   \/_/ \/_/   \/_/\/_/   \/____/   \/_____/ 
                                                                                                                                         
''', id="ascii_art")
        yield Horizontal(
            Button("Home", id="home_btn", flat=True),
            Button("Add", id="add_btn", flat=True),
            Button("Search", id="search_btn", flat=True),
            Button("Sort", id="sort_btn", flat=True),
            Button("Tags", id="tags_btn", flat=True),
            Button("Info", id="info_btn", flat=True),
            id="menu_bar"
        )
        yield Container(id="main_area")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "LinkDB"
        self.sub_title = "Save links easily"
        self._sort_mode = getattr(self, '_sort_mode', 'id_asc')
        self.show_main_list()

    def show_main_list(self, tag_filter=None):
        main_area = self.query_one("#main_area", Container)
        # Explicitly remove all children and refresh to avoid duplicate IDs
        for child in list(main_area.children):
            child.remove()
        main_area.refresh()
        import uuid
        unique = str(uuid.uuid4())[:8]
        folders, bookmarks = get_folders_and_bookmarks()
        if tag_filter:
            bookmarks = [
                b for b in bookmarks
                if tag_filter in [t.strip() for t in (b[5] or '').replace(';', ',').replace(' ', ',').split(',') if t.strip()]
            ]
        # Sort bookmarks according to self._sort_mode
        mode = getattr(self, '_sort_mode', 'id_asc')
        if mode == "id_asc":
            bookmarks = sorted(bookmarks, key=lambda b: b[0])
        elif mode == "id_desc":
            bookmarks = sorted(bookmarks, key=lambda b: b[0], reverse=True)
        elif mode == "title_az":
            bookmarks = sorted(bookmarks, key=lambda b: (b[2] or '').lower())
        elif mode == "title_za":
            bookmarks = sorted(bookmarks, key=lambda b: (b[2] or '').lower(), reverse=True)
        list_items = []
        if folders:
            list_items.append(Static("Folders:"))
            for fid, name in folders:
                list_items.append(Static(f"📁 {name}", id=f"folder_{fid}"))
        if bookmarks:
            list_items.append(Static("Bookmarks:"))
            bookmark_items = []
            for bid, url, title, folder_id, color, tags in bookmarks:
                display = f"[ID:{bid}] [{color}]{title or ''}[/{color}]"
                item = ListItem(Label(display, id=f"bookmark_{bid}"), id=f"bookmark_item_{bid}")
                item.url = url
                item.tags = tags
                bookmark_items.append(item)
            # Use a unique ID for the ListView to avoid DuplicateIds
            list_items.append(ListView(*bookmark_items, id=f"bookmark_list_{unique}"))
        if not folders and not bookmarks:
            list_items.append(Static("No folders or bookmarks yet.", id="empty_label"))
        for item in list_items:
            main_area.mount(item)
        self._main_list_unique = unique

    def show_add_form(self):
        main_area = self.query_one("#main_area", Container)
        for child in list(main_area.children):
            child.remove()
        import uuid
        unique = str(uuid.uuid4())[:8]
        main_area.mount(
            Static("Add Bookmarks (paste one or more links separated by space, comma, or semicolon)", id=f"add_form_title_{unique}"),
            Input(placeholder="Paste links here", id=f"links_input_{unique}"),
            Input(placeholder="Tags (comma or space separated)", id=f"tags_input_{unique}"),
            Button("Save", id=f"save_btn_{unique}", variant="success", flat=True),
            Button("Cancel", id=f"cancel_btn_{unique}", variant="error", flat=True),
            Static("", id=f"add_error_{unique}")
        )
        self._add_form_ids = unique

    def show_edit_form(self, item):
        main_area = self.query_one("#main_area", Container)
        for child in list(main_area.children):
            child.remove()
        import uuid
        import re
        from textual.widgets import Select
        unique = str(uuid.uuid4())[:8]
        url = getattr(item, "url", "")
        label_widget = item.query_one("Label")
        display = getattr(label_widget, "renderable", getattr(label_widget, "text", ""))
        color_title = re.search(r"\[\w+\](.*?)\[/\w+\]", display)
        color = re.search(r"\[(\w+)\].*?\[/\w+\]", display)
        if color_title and color:
            title = color_title.group(1).strip()
            color = color.group(1)
        else:
            title = display.strip()
            color = "white"
        # Fallback: if title is blank, get from DB
        tags = ""
        if not title or not hasattr(item, "tags"):
            from db import get_folders_and_bookmarks
            _, bookmarks = get_folders_and_bookmarks()
            for bid, b_url, b_title, folder_id, b_color, b_tags in bookmarks:
                if b_url == url:
                    title = b_title or url
                    color = b_color or "white"
                    tags = b_tags or ""
                    break
        else:
            tags = getattr(item, "tags", "")
        color_options = [
            ("Red", "red"),
            ("Green", "green"),
            ("Yellow", "yellow"),
            ("Blue", "blue"),
            ("Magenta", "magenta"),
            ("Cyan", "cyan"),
            ("White", "white"),
        ]
        main_area.mount(
            Static("Edit Bookmark", id=f"edit_form_title_{unique}"),
            Input(value=title, placeholder="Title", id=f"edit_title_{unique}"),
            Select(options=color_options, value=color, id=f"edit_color_{unique}"),
            Input(value=tags, placeholder="Tags (comma or space separated)", id=f"edit_tags_{unique}"),
            Button("Save", id=f"edit_save_btn_{unique}", variant="success", flat=True),
            Button("Cancel", id=f"edit_cancel_btn_{unique}", variant="error", flat=True),
            Static("", id=f"edit_error_{unique}")
        )
        self._edit_form_ids = unique
        self._edit_url = url

    def show_search_ui(self, query: str = ""):
        main_area = self.query_one("#main_area", Container)
        # Remove all children and refresh to avoid duplicate IDs
        for child in list(main_area.children):
            child.remove()
        main_area.refresh()
        import uuid
        unique = str(uuid.uuid4())[:8]
        # Only show the search bar and buttons initially
        main_area.mount(
            Static("Search Bookmarks", id=f"search_form_title_{unique}"),
            Input(value=query, placeholder="Type to search (title or url)", id=f"search_input_{unique}"),
            Button("Back", id=f"search_back_btn_{unique}", flat=True),
            Button("Main Menu", id=f"main_menu_btn_{unique}", variant="primary", flat=True)
        )
        self._search_form_ids = unique
        # Always focus the search input
        self.call_later(self._focus_search_ui, False, unique)

    def show_search_results(self, query: str):
        main_area = self.query_one("#main_area", Container)
        for child in list(main_area.children):
            child.remove()
        main_area.refresh()
        import uuid
        unique = str(uuid.uuid4())[:8]
        from db import get_folders_and_bookmarks
        _, bookmarks = get_folders_and_bookmarks()
        q = (query or "").strip().lower()
        results = []
        def match(bookmark):
            bid, url, title, folder_id, color, tags = bookmark
            t = (title or "").strip().lower()
            u = (url or "").strip().lower()
            for word in q.split():
                if word not in t and word not in u:
                    return False
            return True
        filtered = list(filter(match, bookmarks))
        for bid, url, title, folder_id, color, tags in filtered:
            display = f"[ID:{bid}] [{color}]{title or ''}[/{color}]"
            item = ListItem(Label(display, id=f"bookmark_{bid}"), id=f"bookmark_item_{bid}")
            item.url = url
            item.tags = tags
            results.append(item)
        main_area.mount(
            Static(f"Results for: '{query}'", id=f"search_results_title_{unique}"),
        )
        if results:
            main_area.mount(ListView(*results, id=f"bookmark_list_search_{unique}"))
        else:
            main_area.mount(Static("No bookmarks found.", id=f"search_no_results_{unique}"))
        main_area.mount(
            Button("Back", id=f"search_back_btn_{unique}", flat=True),
            Button("Main Menu", id=f"main_menu_btn_{unique}", variant="primary", flat=True)
        )
        self._search_form_ids = unique
        self.call_later(self._focus_search_ui, bool(results), unique)

    def _focus_search_ui(self, has_results, unique):
        try:
            if has_results:
                self.query_one("#bookmark_list_search", ListView).focus()
            else:
                self.query_one(f"#search_input_{unique}", Input).focus()
        except Exception:
            pass

    def on_key(self, event):
        # Only handle bookmarks list navigation and Enter
        bookmark_list = self.get_active_bookmark_list()
        unique = getattr(self, '_search_form_ids', None)
        search_input_id = f"search_input_{unique}" if unique else None
        search_input = None
        if unique and search_input_id:
            try:
                search_input = self.query_one(f"#{search_input_id}", Input)
            except Exception:
                pass
        if search_input and search_input.has_focus:
            if event.key == "enter":
                query = search_input.value.strip()
                self.show_search_results(query)
                return
            elif len(event.key) == 1 or event.key in ("backspace", "delete"):
                # Do not update results live, just update input
                return
        if bookmark_list and bookmark_list.has_focus:
            if event.key == "enter":
                selected = bookmark_list.index
                if selected is not None and selected >= 0:
                    item = bookmark_list.children[selected]
                    if hasattr(item, "url"):
                        webbrowser.open(item.url)

    def action_search(self):
        self.show_search_ui()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Handle dynamic IDs
        if event.button.id.startswith("add_btn"):
            self.show_add_form()
        elif event.button.id.startswith("search_btn"):
            self.show_search_ui()
        elif event.button.id.startswith("sort_btn"):
            self.show_sort_menu()
        elif event.button.id == "sort_id_asc_btn":
            self._sort_mode = "id_asc"
            self.show_main_list()
        elif event.button.id == "sort_id_desc_btn":
            self._sort_mode = "id_desc"
            self.show_main_list()
        elif event.button.id == "sort_title_az_btn":
            self._sort_mode = "title_az"
            self.show_main_list()
        elif event.button.id == "sort_title_za_btn":
            self._sort_mode = "title_za"
            self.show_main_list()
        elif event.button.id.startswith("sort_apply_btn"):
            unique = getattr(self, '_sort_menu_ids', None)
            select_id = f"sort_select_{unique}"
            try:
                select = self.query_one(f"#{select_id}", Select)
                self._sort_mode = select.value
                self.show_main_list()
            except Exception:
                self.show_main_list()
        elif event.button.id.startswith("sort_back_btn"):
            self.show_main_list()
        elif event.button.id == "main_menu_btn":
            self.show_main_list()
        elif event.button.id == "home_btn":
            self.show_main_list()
        elif event.button.id == "info_btn":
            self.show_info_menu()
        elif event.button.id.startswith("save_btn"):
            unique = getattr(self, '_add_form_ids', '')
            links_input_id = f"links_input_{unique}"
            tags_input_id = f"tags_input_{unique}"
            error_id = f"add_error_{unique}"
            links_text = self.query_one(f"#{links_input_id}", Input).value
            tags_text = self.query_one(f"#{tags_input_id}", Input).value
            tags = ','.join([t.strip() for t in tags_text.replace(';',',').replace(' ', ',').split(',') if t.strip()])
            if not tags:
                tags = 'main'
            if links_text:
                import re
                urls = [u.strip() for u in re.split(r'[\s,;]+', links_text) if u.strip()]
                if not tags:
                    self.query_one(f"#{error_id}", Static).update("At least one tag is required.")
                    return
                for url in urls:
                    add_bookmark(url, tags=tags)
                self.show_main_list()
            else:
                self.query_one(f"#{error_id}", Static).update("Links are required.")
                return
        elif event.button.id.startswith("cancel_btn"):
            self.show_main_list()
        elif event.button.id.startswith("edit_save_btn"):
            unique = getattr(self, '_edit_form_ids', '')
            title_input_id = f"edit_title_{unique}"
            color_input_id = f"edit_color_{unique}"
            tags_input_id = f"edit_tags_{unique}"
            error_id = f"edit_error_{unique}"
            title = self.query_one(f"#{title_input_id}", Input).value.strip()
            color = self.query_one(f"#{color_input_id}", Select).value
            tags = self.query_one(f"#{tags_input_id}", Input).value
            tags = ','.join([t.strip() for t in tags.replace(';',',').replace(' ', ',').split(',') if t.strip()])
            if not tags:
                tags = 'main'
            url = getattr(self, '_edit_url', '')
            if not title:
                self.query_one(f"#{error_id}", Static).update("Title cannot be blank.")
                return
            if url:
                from db import update_bookmark
                update_bookmark(url, title, color, tags)
            self.show_main_list()
        elif event.button.id.startswith("edit_cancel_btn"):
            self.show_main_list()
        elif event.button.id.startswith("delete_yes_btn"):
            url = getattr(self, '_pending_delete_url', None)
            if url:
                from db import delete_bookmark
                delete_bookmark(url)
            self.show_main_list()
        elif event.button.id.startswith("delete_no_btn"):
            self.show_main_list()
        elif event.button.id.startswith("search_back_btn"):
            self.show_main_list()
        elif event.button.id.startswith("main_menu_btn"):
            self.show_main_list()
        elif event.button.id.startswith("tags_btn"):
            self.show_tags_menu()
        elif event.button.id.startswith("tags_back_btn"):
            self.show_main_list()
        elif event.button.id.startswith("tag_btn_"):
            tag = event.button.label
            self.show_main_list(tag_filter=tag)
        elif event.button.id.startswith("tags_filter_btn"):
            unique = getattr(self, '_tags_menu_ids', None)
            select_id = f"tags_select_{unique}"
            try:
                select = self.query_one(f"#{select_id}", Select)
                tag = select.value
                self.show_main_list(tag_filter=tag)
            except Exception:
                self.show_main_list()

    def show_sort_menu(self):
        main_area = self.query_one("#main_area", Container)
        for child in list(main_area.children):
            child.remove()
        import uuid
        unique = str(uuid.uuid4())[:8]
        sort_options = [
            ("ID Ascending (Oldest)", "id_asc"),
            ("ID Descending (Newest)", "id_desc"),
            ("Title A-Z", "title_az"),
            ("Title Z-A", "title_za"),
        ]
        main_area.mount(
            Static("Sort Bookmarks", id=f"sort_menu_title_{unique}"),
            Select(options=sort_options, value=self._sort_mode, id=f"sort_select_{unique}"),
            Button("Apply", id=f"sort_apply_btn_{unique}", flat=True),
            Button("Back", id=f"sort_back_btn_{unique}", flat=True)
        )
        self._sort_menu_ids = unique

    def show_tags_menu(self):
        main_area = self.query_one("#main_area", Container)
        for child in list(main_area.children):
            child.remove()
        import uuid
        unique = str(uuid.uuid4())[:8]
        from db import get_folders_and_bookmarks
        _, bookmarks = get_folders_and_bookmarks()
        tag_set = set()
        for _, _, _, _, _, tags in bookmarks:
            for tag in (tags or '').replace(';', ',').replace(' ', ',').split(','):
                tag = tag.strip()
                if tag:
                    tag_set.add(tag)
        tag_list = sorted(tag_set)
        main_area.mount(Static("Filter by Tag", id=f"tags_menu_title_{unique}"))
        if tag_list:
            main_area.mount(Select(options=[(tag, tag) for tag in tag_list], id=f"tags_select_{unique}"))
            main_area.mount(Button("Filter", id=f"tags_filter_btn_{unique}", flat=True))
        else:
            main_area.mount(Static("No tags found.", id=f"tags_menu_empty_{unique}"))
        main_area.mount(Button("Back", id=f"tags_back_btn_{unique}", flat=True))
        self._tags_menu_ids = unique

    def show_info_menu(self):
        main_area = self.query_one("#main_area", Container)
        for child in list(main_area.children):
            child.remove()
        import uuid
        unique = str(uuid.uuid4())[:8]
        main_area.mount(
            Label("LinkDB - A simple bookmark manager", id=f"info_title_{unique}"),
            Label("Made by: Chari69", id=f"info_creator_{unique}"),
            Label("Version: 1.0.0", id=f"info_version_{unique}")
        )
        self._sort_menu_ids = unique

    def get_active_bookmark_list(self):
        main_area = self.query_one("#main_area", Container)
        # Accept any ListView with id starting with 'bookmark_list'
        for child in main_area.children:
            if isinstance(child, ListView) and str(child.id).startswith("bookmark_list"):
                return child
        return None

    def on_key(self, event):
        # Only handle bookmarks list navigation and Enter
        bookmark_list = self.get_active_bookmark_list()
        unique = getattr(self, '_search_form_ids', None)
        search_input_id = f"search_input_{unique}" if unique else None
        search_input = None
        if unique and search_input_id:
            try:
                search_input = self.query_one(f"#{search_input_id}", Input)
            except Exception:
                pass
        if search_input and search_input.has_focus:
            if event.key == "enter":
                query = search_input.value.strip()
                self.show_search_results(query)
                return
            elif len(event.key) == 1 or event.key in ("backspace", "delete"):
                # Do not update results live, just update input
                return
        if bookmark_list and bookmark_list.has_focus:
            if event.key == "enter":
                selected = bookmark_list.index
                if selected is not None and selected >= 0:
                    item = bookmark_list.children[selected]
                    if hasattr(item, "url"):
                        webbrowser.open(item.url)

    def action_up(self):
        bookmark_list = self.get_active_bookmark_list()
        if bookmark_list:
            bookmark_list.action_cursor_up()

    def action_down(self):
        bookmark_list = self.get_active_bookmark_list()
        if bookmark_list:
            bookmark_list.action_cursor_down()

    def action_enter(self):
        bookmark_list = self.get_active_bookmark_list()
        if bookmark_list:
            selected = bookmark_list.index
            if selected is not None and selected >= 0:
                item = bookmark_list.children[selected]
                if hasattr(item, "url"):
                    import webbrowser
                    webbrowser.open(item.url)

    def action_add(self):
        self.show_add_form()

    def action_edit(self):
        bookmark_list = self.get_active_bookmark_list()
        if bookmark_list:
            selected = bookmark_list.index
            if selected is not None and selected >= 0:
                item = bookmark_list.children[selected]
                if hasattr(item, "url"):
                    self.show_edit_form(item)

    def action_delete(self):
        bookmark_list = self.get_active_bookmark_list()
        if bookmark_list:
            selected = bookmark_list.index
            if selected is not None and selected >= 0:
                item = bookmark_list.children[selected]
                if hasattr(item, "url"):
                    self._pending_delete_url = item.url
                    self.show_delete_confirm()

    def show_delete_confirm(self):
        main_area = self.query_one("#main_area", Container)
        for child in list(main_area.children):
            child.remove()
        import uuid
        unique = str(uuid.uuid4())[:8]
        main_area.mount(
            Static("Are you sure you want to delete this bookmark?", id=f"delete_confirm_{unique}"),
            Button("Yes", id=f"delete_yes_btn_{unique}", variant="success", flat=True),
            Button("No", id=f"delete_no_btn_{unique}", variant="error", flat=True),
        )
        self._delete_confirm_ids = unique

    def on_list_view_item_selected(self, event):
        item = event.item
        if hasattr(item, "url"):
            import webbrowser
            webbrowser.open(item.url)
