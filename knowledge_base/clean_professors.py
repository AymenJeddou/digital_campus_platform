import os
import re


def clean_professors_content(file_text):
    """
    Cleans professors folder files (department pages).
    Removes: metadata headers, excessive HTML tags, formatting noise
    Keeps: department info, formations, and professor listings with structured data
    """
    # Remove HTML tags but preserve content
    text = file_text.replace("<br>", " ")
    text = text.replace("<p>", "")
    text = text.replace("</p>", "\n")
    text = text.replace("<table>", "")
    text = text.replace("</table>", "")
    text = text.replace("<tbody>", "")
    text = text.replace("</tbody>", "")
    text = text.replace("<tr>", "\n")
    text = text.replace("</tr>", "")
    text = text.replace("<td>", " | ")
    text = text.replace("</td>", "")
    text = re.sub(r'<[^>]+>', '', text)
    
    # Split into lines
    lines = text.split('\n')
    cleaned_lines = []
    skip_metadata = True  # Skip initial metadata
    
    for i, line in enumerate(lines):
        # Skip metadata headers (Title, Author, Source)
        if any(meta in line for meta in ['**Title:**', '**Author:**', '**Source:**', '---']):
            continue
        
        # Start processing after metadata
        if '---' in lines[max(0, i-5):i]:
            skip_metadata = False
        
        if not line.strip():
            if cleaned_lines and not cleaned_lines[-1].strip():
                continue
            cleaned_lines.append(line)
            continue
        
        # Remove image references
        if line.strip().startswith('!['):
            continue
        
        # Clean up pipe formatting from converted tables
        if '|' in line:
            # Clean table cell format to readable format
            line = line.replace(' | ', ' • ')
            line = line.replace('| | ', '')
        
        cleaned_lines.append(line)
    
    # Join back
    text = '\n'.join(cleaned_lines)
    
    # Normalize multiple spaces
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


if __name__ == "__main__":
    # Clean professors files
    folder_path = "professors"
    
    if not os.path.exists(folder_path):
        print(f"Error: Could not find {folder_path}")
    else:
        print("Starting professors files cleaning...\n")
        
        for filename in os.listdir(folder_path):
            if filename.endswith(".md"):
                input_path = os.path.join(folder_path, filename)
                output_filename = filename.replace(".md", "_cleaned.md")
                output_path = os.path.join(folder_path, output_filename)
                
                print(f"{'='*50}")
                print(f"Cleaning: {filename}")
                print(f"{'='*50}")
                
                # Read file
                with open(input_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Clean content
                cleaned_content = clean_professors_content(content)
                
                # Write cleaned file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                
                # Stats
                original_lines = content.count('\n')
                cleaned_lines = cleaned_content.count('\n')
                reduction = ((original_lines - cleaned_lines) / original_lines * 100) if original_lines > 0 else 0
                
                print(f"Original lines: {original_lines}")
                print(f"Cleaned lines: {cleaned_lines}")
                print(f"Reduction: {reduction:.1f}%")
                print(f"Output saved to: {output_path}\n")
                
                # Preview
                print("Preview of cleaned content:")
                print("-" * 50)
                print(cleaned_content[:400])
                print("-" * 50)
                print()
