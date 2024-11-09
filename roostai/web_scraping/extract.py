import os
from bs4 import BeautifulSoup
import shutil


def extract_main_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements like scripts, styles, and comments
    for element in soup(["script", "style", "comment"]):
        element.extract()
    
    # Process all links before getting the text
    for link in soup.find_all('a'):
        # Get the link text and href
        text = link.get_text(strip=True)
        href = link.get('href', '')
        
        # Only process if there's both text and href
        if text and href:
            # Replace the link with text(link) format
            # Preserve the link's position in the document
            link.replace_with(f"{text}({href})")
    
    # Extract the text content, excluding boilerplate elements
    relevant_text = soup.get_text(strip=True)
    
    return relevant_text
  
    # main_tag = soup.find('main')
    
    # # Extract the text within the <main> tag                      
    # if main_tag:
    #     return main_tag.get_text(separator=' ', strip=True)
    # else:
    #     return ""  # Return empty string if <main> tag is not found


def save_text_to_file(text, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(text)


def process_html_files(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i, file_name in enumerate(os.listdir(input_dir), 1):
        if not file_name.endswith('html'):
          source_file = os.path.join(input_dir, file_name)
          dest_file = os.path.join(output_dir, file_name)
          shutil.copy2(source_file, dest_file) 
          continue
        
        input_file_path = os.path.join(input_dir, file_name)
        
        file_name_without_extension, _= file_name.split('.')
        output_file_path = os.path.join(output_dir, f'{file_name_without_extension}.txt')

        with open(input_file_path, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()

        main_text = extract_main_text(html_content)
        save_text_to_file(main_text, output_file_path)

        print(f"Processed {file_name} and saved to {output_file_path}")


if __name__ == "__main__":
  # Example usage
  input_directory = '/home/cc/collected_data'
  output_directory = '/home/cc/extracted_data'
  process_html_files(input_directory, output_directory)
  print("Main text extracted!")
