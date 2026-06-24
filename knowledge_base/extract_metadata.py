import os
import re
import json
from datetime import datetime


def extract_metadata(file_path, folder_name):
    """
    Extract metadata from a markdown file.
    Returns: dict with title, source, total_pages, file_info
    """
    metadata = {
        "filename": os.path.basename(file_path),
        "folder": folder_name,
        "file_path": file_path,
        "extraction_date": datetime.now().isoformat(),
        "title": None,
        "source": None,
        "line_count": 0,
        "byte_count": 0,
    }
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Get file stats
        lines = content.split('\n')
        metadata["line_count"] = len(lines)
        metadata["byte_count"] = len(content)
        
        # Extract title (look for # heading or filename)
        title_match = re.search(r'^#+\s+(.+?)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Skip if it looks like OCR garbage (mostly special chars)
            if sum(1 for c in title if c.isalnum()) > len(title) / 3:
                metadata["title"] = title
            else:
                # Use filename as fallback
                metadata["title"] = os.path.splitext(os.path.basename(file_path))[0]
        else:
            # Use filename as title
            metadata["title"] = os.path.splitext(os.path.basename(file_path))[0]
        
        # Extract source (look for Source: or http links)
        source_match = re.search(r'\*?\*?Source:?\*?\*?\s*(\[.*?\]\((.*?)\)|(https?://\S+))', content)
        if source_match:
            if source_match.group(2):  # URL in brackets
                metadata["source"] = source_match.group(2)
            elif source_match.group(3):  # Direct URL
                metadata["source"] = source_match.group(3)
        
        # Note: total_pages removed - not useful for markdown files
        
        return metadata
    
    except Exception as e:
        metadata["error"] = str(e)
        return metadata


def extract_all_metadata(base_path=".", json_output="metadata.json", csv_output="metadata.csv"):
    """
    Extract metadata ONLY from cleaned markdown files in the knowledge base.
    Saves to both JSON and CSV formats.
    """
    all_metadata = {
        "extraction_timestamp": datetime.now().isoformat(),
        "documents": [],
        "summary": {
            "total_documents": 0,
            "documents_by_folder": {},
            "total_lines": 0,
            "total_bytes": 0,
        }
    }
    
    # Define folders and scan ONLY clean subfolders
    folders_structure = {
        "course_and_admission": "clean",
        "orientation": "clean",
        "professors": "clean",
    }
    
    for main_folder, subfolder in folders_structure.items():
        folder_path = os.path.join(base_path, main_folder, subfolder)
        folder_label = f"{main_folder}"
        
        if not os.path.exists(folder_path):
            print(f"Warning: Folder not found: {folder_path}")
            continue
        
        print(f"\n{'='*60}")
        print(f"Processing: {folder_label} (clean)")
        print(f"{'='*60}")
        
        all_metadata["summary"]["documents_by_folder"][folder_label] = 0
        
        for filename in sorted(os.listdir(folder_path)):
            if filename.endswith(".md"):
                file_path = os.path.join(folder_path, filename)
                
                # Extract metadata
                metadata = extract_metadata(file_path, folder_label)
                all_metadata["documents"].append(metadata)
                
                # Update summary
                all_metadata["summary"]["total_documents"] += 1
                all_metadata["summary"]["documents_by_folder"][folder_label] += 1
                all_metadata["summary"]["total_lines"] += metadata["line_count"]
                all_metadata["summary"]["total_bytes"] += metadata["byte_count"]
                
                # Print info
                print(f"\n📄 {metadata['filename']}")
                print(f"   Title: {metadata['title']}")
                if metadata['source']:
                    print(f"   Source: {metadata['source']}")
                print(f"   Lines: {metadata['line_count']:,}")
                print(f"   Bytes: {metadata['byte_count']:,}")
    
    # Save as JSON
    json_path = os.path.join(base_path, json_output)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, indent=2, ensure_ascii=False)
    
    # Save as CSV
    csv_path = os.path.join(base_path, csv_output)
    import csv as csv_module
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if all_metadata["documents"]:
            writer = csv_module.DictWriter(
                f,
                fieldnames=[
                    "filename",
                    "folder",
                    "title",
                    "source",
                    "line_count",
                    "byte_count",
                    "file_path",
                    "extraction_date"
                ]
            )
            writer.writeheader()
            for doc in all_metadata["documents"]:
                writer.writerow(doc)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total Documents (Clean): {all_metadata['summary']['total_documents']}")
    print(f"Total Lines: {all_metadata['summary']['total_lines']:,}")
    print(f"Total Bytes: {all_metadata['summary']['total_bytes']:,}")
    print(f"\nDocuments by Folder:")
    for folder, count in all_metadata['summary']['documents_by_folder'].items():
        print(f"  - {folder}: {count} documents")
    print(f"\nMetadata saved to:")
    print(f"  - JSON: {json_path}")
    print(f"  - CSV: {csv_path}")
    
    return all_metadata


def print_metadata_table(metadata_list):
    """
    Print metadata in a table format.
    """
    print(f"\n\n{'='*100}")
    print(f"CLEANED DOCUMENTS METADATA TABLE")
    print(f"{'='*100}\n")
    print(f"{'Filename':<40} {'Title':<35} {'Lines':<10} {'Bytes':<12}")
    print("-" * 100)
    
    for doc in metadata_list:
        filename = doc['filename'][:39]
        title = (doc['title'][:34] if doc['title'] else 'N/A')
        lines = f"{doc['line_count']:,}"
        bytes_size = f"{doc['byte_count']:,}"
        
        print(f"{filename:<40} {title:<35} {lines:<10} {bytes_size:<12}")


if __name__ == "__main__":
    # Extract metadata from ONLY cleaned documents
    metadata = extract_all_metadata(
        json_output="metadata.json",
        csv_output="metadata.csv"
    )
    
    # Print table
    print_metadata_table(metadata["documents"])
