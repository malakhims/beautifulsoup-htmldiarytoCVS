from bs4 import BeautifulSoup
import os
import csv
import re
from datetime import datetime

# ======== CONFIGURATION ========
HTML_DIR = r"C:\Users\TJ\Desktop\CODE\diary_python\diary"
OUTPUT_CSV = r"C:\Users\TJ\Desktop\CODE\diary_python\diaryentriesspreadsheet.csv"
# ===============================

def parse_date_title(header_text):
    """Specialized parser for your exact date format"""
    # Split title and date (handles both " - " and "|" separators)
    if ' - ' in header_text:
        date_part, title = [x.strip() for x in header_text.split(' - ', 1)]
    elif '|' in header_text:
        date_part, title = [x.strip() for x in header_text.split('|', 1)]
    else:
        return header_text.strip(), header_text.strip()  # For manual review
    
    # ===== NEW IMPROVED DATE PARSING =====
    # Case 1: Already in SQL format (YYYY-MM-DD HH:MM:SS)
    sql_date_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', date_part)
    if sql_date_match:
        return sql_date_match.group(1), title  # Return as-is
    
    # Case 2: MM/DD/YYYY format (convert to SQL)
    slash_date_match = re.search(r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})', date_part)
    if slash_date_match:
        date_obj = datetime.strptime(slash_date_match.group(1), '%m/%d/%Y %H:%M:%S')
        return date_obj.strftime('%Y-%m-%d %H:%M:%S'), title
    
    # Case 3: Fallback (return original for manual review)
    return date_part, title

def parse_entries(html_content):
    """Handles all formats (TITLE:/DATE:/BODY: or HTML)"""
    if "TITLE:" in html_content and "DATE:" in html_content:
        return parse_text_format(html_content)
    else:
        return parse_html_format(html_content)

def parse_text_format(text):
    """For 'TITLE: x DATE: y BODY: z' format"""
    entries = []
    pattern = r'TITLE:\s*(.*?)\s*DATE:\s*(.*?)\s*BODY:\s*(.*?)(?=(TITLE:|DATE:|$))'
    for match in re.finditer(pattern, text, re.DOTALL):
        # Clean date string first
        raw_date = re.sub(r'-----.+$', '', match.group(2)).strip()
        date_str, _ = parse_date_title(raw_date)  # Reuse our main parser
        
        entries.append({
            'id': '',
            'title': match.group(1).strip(),
            'content': match.group(3).strip(),
            'post_date': date_str,
            'updated_at': date_str,
            'category': 'Uncategorized',
            'tags': '',
            'anchor_name': generate_anchor(date_str)
        })
    return entries

def parse_html_format(html):
    """For <div class="diarycontent"><b>DATE - TITLE</b>...</div> format"""
    soup = BeautifulSoup(html, 'html.parser')
    entries = []
    
    for entry in soup.find_all('div', class_='diarycontent'):
        header = entry.find('b')
        if header:
            post_date, title = parse_date_title(header.get_text(strip=True))
        else:
            post_date, title = "1970-01-01 00:00:00", "Untitled"
        
        # Extract content after <hr>
        content = []
        hr = entry.find('hr')
        if hr:
            for sibling in hr.next_siblings:
                if sibling.name == 'div' and 'diarycontent' in sibling.get('class', []):
                    break
                content.append(str(sibling))
        else:
            content = [str(child) for child in entry.children if child.name != 'b']
        
        entries.append({
            'id': '',  # AUTO_INCREMENT
            'title': title,
            'content': ''.join(content).strip(),
            'post_date': post_date,
            'updated_at': post_date,
            'category': 'Uncategorized',
            'tags': '',
            'anchor_name': generate_anchor(post_date)
        })
    
    return entries

def generate_anchor(date_str):
    """Creates anchor like 'may2025_9' from YYYY-MM-DD"""
    try:
        dt = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
        return dt.strftime('%b%Y_%d').lower()
    except:
        return "unknown"

def main():
    print("=== Database-Ready Diary Parser ===")
    
    if not os.path.exists(HTML_DIR):
        print(f"❌ ERROR: Folder not found: {HTML_DIR}")
        return
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        # EXACT column order matching your database
        writer = csv.DictWriter(csvfile, fieldnames=[
            'id', 'title', 'content', 'post_date', 
            'updated_at', 'category', 'tags', 'anchor_name'
        ])
        writer.writeheader()
        
        for filename in os.listdir(HTML_DIR):
            if filename.lower().endswith('.html'):
                filepath = os.path.join(HTML_DIR, filename)
                print(f"Processing: {filename}")
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        entries = parse_entries(f.read())
                    
                    writer.writerows(entries)
                    print(f"✓ Added {len(entries)} entries")
                
                except Exception as e:
                    print(f"⚠️ Error in {filename}: {str(e)}")
    
    print(f"\n✅ Done! Output: {OUTPUT_CSV}")
    print("Import to PHPMyAdmin with:")
    print("1. Format: CSV")
    print("2. Columns enclosed by \"")
    print("3. First line contains column names")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")