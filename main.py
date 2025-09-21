from db import init_db
from ui import BookmarkApp

if __name__ == "__main__":
    init_db()
    app = BookmarkApp()
    app.run()
