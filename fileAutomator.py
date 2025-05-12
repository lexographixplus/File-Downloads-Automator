from os import scandir, makedirs
from os.path import splitext, exists, join
from shutil import move
from time import sleep
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ======== CONFIGURATION ========
base_dir = "C:\\Users\\B.E Janko Jnr\\Downloads"

source_dir = base_dir
dest_dir_sfx = join(base_dir, "SFX")
dest_dir_music = join(base_dir, "Music")
dest_dir_video = join(base_dir, "Videos")
dest_dir_image = join(base_dir, "Images")
dest_dir_documents = join(base_dir, "Documents")

# ======== SUPPORTED EXTENSIONS ========
image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico"]
video_extensions = [".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm"]
audio_extensions = [".mp3", ".wav", ".aac", ".flac", ".m4a", ".wma"]
document_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"]

# ======== UTILITIES ========
def make_unique(dest, name):
    filename, extension = splitext(name)
    counter = 1
    while exists(join(dest, name)):
        name = f"{filename}({counter}){extension}"
        counter += 1
    return name

def move_file(dest, entry, name):
    try:
        target_path = join(dest, name)
        if exists(target_path):
            name = make_unique(dest, name)
            target_path = join(dest, name)
        move(entry.path, target_path)
        logging.info(f"Moved: {name} -> {dest}")
    except Exception as e:
        logging.error(f"Failed to move {name}: {e}")

def ensure_dirs_exist():
    for folder in [dest_dir_sfx, dest_dir_music, dest_dir_video, dest_dir_image, dest_dir_documents]:
        makedirs(folder, exist_ok=True)

# ======== EVENT HANDLER ========
class MoverHandler(FileSystemEventHandler):
    def process_event(self):
        sleep(1)  # wait for file to finish downloading
        with scandir(source_dir) as entries:
            for entry in entries:
                name = entry.name
                if entry.is_file() and not name.lower().endswith(('.crdownload', '.tmp', '.part')):
                    self.route_file(entry, name)

    def on_created(self, event):
        self.process_event()

    def on_modified(self, event):
        self.process_event()

    def route_file(self, entry, name):
        ext = splitext(name)[1].lower()
        size = entry.stat().st_size

        if ext in audio_extensions:
            dest = dest_dir_sfx if size < 10_000_000 or "SFX" in name.upper() else dest_dir_music
            move_file(dest, entry, name)
        elif ext in video_extensions:
            move_file(dest_dir_video, entry, name)
        elif ext in image_extensions:
            move_file(dest_dir_image, entry, name)
        elif ext in document_extensions:
            move_file(dest_dir_documents, entry, name)
        else:
            logging.info(f"Skipped unhandled file: {name}")

# ======== MAIN RUNNER ========
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    ensure_dirs_exist()
    logging.info(f"Started monitoring folder: {source_dir}")

    event_handler = MoverHandler()
    event_handler.process_event()  # Handle files already in the folder on startup

    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=False)
    observer.start()

    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Monitoring stopped by user.")
    observer.join()
