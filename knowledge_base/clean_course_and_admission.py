
import os
import re

def clean_fsb_ci_and_prog_info(file_text):
    """
    Cleans FSB-CI.md and Prog_Info_Integré.md files.
    Removes: page numbers, TOCs, metadata, excessive whitespace
    Keeps: meaningful content organized by sections
    """
    # Remove standalone page numbers (often on their own line)
    text = re.sub(r'^\s*\d+\s*$', '', file_text, flags=re.MULTILINE)
    
    # Remove common HTML tags
    text = text.replace("<br>", " ")
    text = re.sub(r'<[^>]+>', '', text)
    
    # Split into lines for processing
    lines = text.split('\n')
    cleaned_lines = []
    skip_toc = False
    
    for i, line in enumerate(lines):
        # Skip table of contents sections (lines with lots of dots)
        if '........................' in line or 'TABLE DES MATIERES' in line.upper():
            skip_toc = True
            continue
        
        # Skip lines that are just dots and pipes (TOC formatting)
        if re.match(r'^[\|\.]+$', line.strip()):
            skip_toc = False
            continue
        
        # Skip excessive blank lines (keep max 2 consecutive)
        if not line.strip():
            if cleaned_lines and not cleaned_lines[-1].strip():
                continue
            cleaned_lines.append(line)
            continue
        
        # Keep the line
        if line.strip():
            cleaned_lines.append(line)
    
    # Join lines back
    text = '\n'.join(cleaned_lines)
    
    # Normalize multiple spaces to single space within paragraphs
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # Remove excessive newlines (more than 2 in a row)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def clean_and_chunk_course_admission(file_text):
    """
    Cleans and chunks files from the course_and_admission folder.
    Handles narrative text, drops TOCs, and flattens structured syllabus tables.
    """
    chunks = []
    
    # Remove standalone page numbers on lines
    text = re.sub(r'^\s*\d+\s*$', '', file_text, flags=re.MULTILINE)
    text = text.replace("<br>", " ")
    
    # Split text into structural blocks
    raw_blocks = text.split("\n\n")
    
    current_section_title = "General"
    current_ue_type = "Fondamentale" 
    current_ue_name = ""

    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
            
        # Track Section Headings
        if block.startswith("#"):
            current_section_title = block.replace("#", "").strip()
            chunks.append(f"Context: {current_section_title}\n{block}")
            continue

        # Handle Tables
        if block.startswith("|"):
            if "TABLE DES MATIERES" in block or "....." in block:
                continue
                
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            
            for line in lines:
                if '---|' in line:
                    continue
                    
                cols = [c.strip() for c in line.split('|')[1:-1]]
                if not cols or len(cols) < 2:
                    continue
                    
                if "Unités" in cols[0] or "Cours" in cols[2] or "Total" in cols[0]:
                    continue
                
                if "U.E." in cols[0] and not cols[1]:
                    current_ue_type = cols[0].replace("**", "").strip()
                    continue
                    
                if cols[0]:
                    current_ue_name = cols[0].replace("**", "").strip()
                
                ecue_name = cols[1].replace("**", "").strip()
                
                if ecue_name:
                    total_hours = cols[6] if len(cols) > 6 and cols[6] else "Non spécifié"
                    ecue_credits = cols[7] if len(cols) > 7 and cols[7] else "N/A"
                    ue_credits = cols[8] if len(cols) > 8 and cols[8] else "N/A"
                    ecue_coef = cols[9] if len(cols) > 9 and cols[9] else "N/A"
                    
                    flattened_row = (
                        f"Programme: {current_section_title} | "
                        f"Type d'Unité: {current_ue_type} | "
                        f"Unité d'Enseignement (UE): {current_ue_name} | "
                        f"Élément (ECUE): {ecue_name} | "
                        f"Volume Horaire Total: {total_hours}h | "
                        f"Crédits ECUE: {ecue_credits} (Total UE: {ue_credits}) | "
                        f"Coefficient ECUE: {ecue_coef}"
                    )
                    chunks.append(flattened_row)
            continue

        # Handle standard narrative text
        clean_paragraph = re.sub(r'\s+', ' ', block)
        chunks.append(f"Context: {current_section_title}\n{clean_paragraph}")

    return chunks


if __name__ == "__main__":
    # Clean FSB-CI.md and Prog_Info_Integré.md
    files_to_clean = [
        ("course_and_admission/FSB-CI.md", "course_and_admission/FSB-CI_cleaned.md"),
        ("course_and_admission/Prog_Info_Integré.md", "course_and_admission/Prog_Info_Integré_cleaned.md"),
    ]
    
    print("Starting cleaning process...\n")
    
    for input_file, output_file in files_to_clean:
        if not os.path.exists(input_file):
            print(f"Error: Could not find {input_file}")
            continue
        
        print(f"{'='*50}")
        print(f"Cleaning: {input_file}")
        print(f"{'='*50}")
        
        # Read the file
        with open(input_file, "r", encoding="utf-8") as f:
            file_content = f.read()
        
        # Clean the content
        cleaned_content = clean_fsb_ci_and_prog_info(file_content)
        
        # Write to cleaned file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_content)
        
        # Show stats
        original_lines = file_content.count('\n')
        cleaned_lines = cleaned_content.count('\n')
        reduction = ((original_lines - cleaned_lines) / original_lines * 100) if original_lines > 0 else 0
        
        print(f"Original lines: {original_lines}")
        print(f"Cleaned lines: {cleaned_lines}")
        print(f"Reduction: {reduction:.1f}%")
        print(f"Output saved to: {output_file}\n")
        
        # Preview first 500 characters
        print("Preview of cleaned content:")
        print("-" * 50)
        print(cleaned_content[:500])
        print("-" * 50)
        print()

