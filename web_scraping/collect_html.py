import os
import shutil

def collect_html_files(source_dir, destination_dir):
    # Create destination directory if it doesn't exist
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Track filenames to handle duplicates

    # Walk through all subdirectories in the source directory
    # os.walk is DFS traversal of a directory
    counter = 1
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".html"):
                # source file path
                source_file_path = os.path.join(root, file)
                
                # dest file path
                destination_file_path = os.path.join(destination_dir, f"scraped_html_{counter}")
                
                # Copy the file to the new location
                shutil.copy2(source_file_path, destination_file_path)

                print(f"Copied: {source_file_path} -> {destination_file_path}")
                counter +=1


if __name__ == "__main__":
    source_directory = "/home/cc/scraped_data"  # Replace with your source directory
    destination_directory = "/home/cc/scraped_data2"  # Replace with your destination directory

    collect_html_files(source_directory, destination_directory)
