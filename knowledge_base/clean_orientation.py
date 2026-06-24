import os
import re


def clean_orientation_content(file_text):
    """
    Cleans orientation folder files (guide2025.md).
    Removes: OCR artifacts, page numbers, image references, formatting noise
    Keeps: meaningful guidance content and structured sections in Arabic
    """
    text = file_text
    
    # Remove OCR artifacts - check first few lines
    lines = text.split('\n')
    start_idx = 0
    
    # Skip garbage header lines (starting with # and containing mostly special chars/OCR)
    for i, line in enumerate(lines[:5]):  # Check first 5 lines
        if line.strip().startswith('#'):
            # Count non-letter, non-digit chars (indicating garbage)
            letters_digits = sum(1 for c in line if c.isalnum())
            if letters_digits < len(line.strip()) / 2:  # More than half is garbage chars
                start_idx = i + 1
            else:
                break
        elif line.strip() and not line.strip().startswith('#'):
            break
    
    text = '\n'.join(lines[start_idx:])
    
    # Remove standalone image placeholders and their OCR text
    text = re.sub(r'==> picture \[[\d\s\w]+\] intentionally omitted <==.*?(?=\n(?:##|#|\-|• |[A-Za-z0-9]|$))', 
                  '', text, flags=re.DOTALL)
    text = re.sub(r'----- Start of picture text -----.*?----- End of picture text -----', '', text, flags=re.DOTALL)
    
    # Remove HTML tags
    text = text.replace("<br>", " ")
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove image references and their OCR text
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    
    # Remove lines with mostly special characters, garbage OCR, or formatting noise
    lines = text.split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        original_line = line
        
        # Skip lines with OCR garbage (lots of special characters mixed)
        if re.search(r'[oa>e<\|~]{5,}', line):  # OCR artifacts
            continue
        
        # Skip email-like metadata and pure URL lines
        if line.strip().startswith('www.') or line.strip().startswith('http'):
            # Keep URLs that are relevant (like guidance website), skip others in metadata
            if 'orientation' not in line.lower() and 'formation' not in line.lower():
                continue
        
        # Skip lines that are just numbers/formatting/special chars
        if re.match(r'^[\s\|\\\*\.\-\+\=\)]+$', line):
            continue
        
        # Skip lines with excessive special character noise
        if len(line.strip()) > 5:
            special_chars = len(re.findall(r'[~\|><\*\^\`]', line))
            if special_chars > len(line.strip()) / 3:
                continue
        
        # Skip random garbled text (OCR artifacts)
        if re.match(r'^[oa]{1,3}\s*[a-zA-Z0-9\>\<\|]*\s*$', line):
            continue
        
        # Handle excessive empty lines
        if not line.strip():
            if cleaned_lines and not cleaned_lines[-1].strip():
                continue
            cleaned_lines.append(line)
            continue
        
        # Skip pure number lines (page numbers)
        if re.match(r'^\s*\d+\s*$', line):
            continue
        
        cleaned_lines.append(original_line)
    
    # Join back
    text = '\n'.join(cleaned_lines)
    
    # Clean up markdown tables that got corrupted
    text = re.sub(r'\|\|+', '|', text)
    text = re.sub(r'\|\s*---\s*\|', '| --- |', text)
    
    # Normalize multiple spaces within lines (but preserve indentation intent)
    lines = text.split('\n')
    normalized_lines = []
    for line in lines:
        if line.strip():
            # Preserve leading spaces for lists/indentation
            leading_spaces = len(line) - len(line.lstrip())
            content = line.strip()
            # Normalize multiple spaces in content to single space
            content = re.sub(r'[ \t]{2,}', ' ', content)
            normalized_lines.append(' ' * leading_spaces + content)
        else:
            normalized_lines.append(line)
    
    text = '\n'.join(normalized_lines)
    
    # Remove excessive newlines (more than 2 in a row)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean up the start/end
    text = text.strip()
    
    return text


if __name__ == "__main__":
    # Clean orientation files from the raw folder
    input_folder = "orientation/raw"
    output_folder = "orientation/clean"
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    if not os.path.exists(input_folder):
        print(f"Error: Could not find {input_folder}")
    else:
        print("Starting orientation files cleaning...\n")
        
        for filename in os.listdir(input_folder):
            if filename.endswith(".md"):
                input_path = os.path.join(input_folder, filename)
                output_filename = filename.replace(".md", "_cleaned.md")
                output_path = os.path.join(output_folder, output_filename)
                
                print(f"{'='*60}")
                print(f"Cleaning: {filename}")
                print(f"{'='*60}")
                
                # Read file
                with open(input_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Clean content
                cleaned_content = clean_orientation_content(content)
                
                # Write cleaned file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                
                # Stats
                original_lines = content.count('\n')
                cleaned_lines = cleaned_content.count('\n')
                original_size = len(content)
                cleaned_size = len(cleaned_content)
                reduction_lines = ((original_lines - cleaned_lines) / original_lines * 100) if original_lines > 0 else 0
                reduction_size = ((original_size - cleaned_size) / original_size * 100) if original_size > 0 else 0
                
                print(f"Original: {original_lines} lines ({original_size:,} bytes)")
                print(f"Cleaned:  {cleaned_lines} lines ({cleaned_size:,} bytes)")
                print(f"Reduction: {reduction_lines:.1f}% lines | {reduction_size:.1f}% size")
                print(f"Output saved to: {output_path}\n")
                
                # Preview
                print("Preview of cleaned content (first 600 chars):")
                print("-" * 60)
                preview = cleaned_content[:600]
                print(preview)
                if len(cleaned_content) > 600:
                    print("...")
                print("-" * 60)
                print()

