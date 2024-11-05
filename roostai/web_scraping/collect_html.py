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
        if 'metadata.json' not in files:
          print('Metadata not found')
          print(root)
          print(files)
        elif 'scraped_data.html' not in files:
          print('HTML not found')
          print(root)
          print(files)
          
        for file in files:
            if file.endswith(".html") or file.endswith('.json'):
                # source file path
                source_file_path = os.path.join(root, file)
                
                # dest file path
                if file.endswith(".html"):
                  destination_file_path = os.path.join(destination_dir, f"scraped_html_{counter}.html")
                else:
                  destination_file_path = os.path.join(destination_dir, f"metadata_{counter}.json")
                 
                # Copy the file to the new location
                shutil.copy2(source_file_path, destination_file_path)

                # print(f"Copied: {source_file_path} -> {destination_file_path}")
        counter +=1


if __name__ == "__main__":
    source_directory = "/home/cc/scraped_data"  # Replace with your source directory
    destination_directory = "/home/cc/collected_data"  # Replace with your destination directory

    collect_html_files(source_directory, destination_directory)
