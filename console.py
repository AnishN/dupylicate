import os
from dupylicate.ui import *
from dupylicate.io import *

def get_files(include_dirs, exclude_dirs):
    include_files = []
    exclude_files = []
    for include_dir in include_dirs:
        for dir_path, dir_names, file_names in os.walk(include_dir):
            include_files.extend([os.path.join(dir_path, file_name).encode("utf-8") for file_name in file_names])
    for exclude_dir in exclude_dirs:
        for dir_path, dir_names, file_names in os.walk(exclude_dir):
            exclude_files.extend([os.path.join(dir_path, file_name).encode("utf-8") for file_name in file_names])
    files = sorted(list(set(include_files) - set(exclude_files)))
    return files

if __name__ == "__main__":
    include_dirs = ["/home/anish/Videos/a"]
    exclude_dirs = ["/home/anish/Videos/a/Deviantart"]
    files = get_files(include_dirs, exclude_dirs)
    num_files = len(files)
    scanner = VideoScanner(
        include_images=True,
        include_videos=True,
        thumbnail_width=16,
        thumbnail_height=16,
        num_thumbnails=3,
        similarity=0.95,
        seek_exact=False,
    )
    scanner.startup(files)
    for i, file in enumerate(files):
        print(i, num_files, file)
        scanner.extract_file_thumbnails(i)
    scanner.cleanup()