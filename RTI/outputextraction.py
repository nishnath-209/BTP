import re
import json
import os
from pdfminer.high_level import extract_text

def question_to_files(question_numbers):
    """
    Converts question numbers to file numbers using the definitive logic:
    - Inverse relationship (q_no down, file_no up).
    - Anchored at file 4371 for the q=1-375 block.
    - Handles specific anomalous questions.
    """
    # --- Step 1: Build the definitive mapping for questions 1-375 ---

    # Anomalous questions that only have one unstarred file
    anomalous_unstarred_only = {64, 113, 123, 215}

    file_map = {}
    
    # NEW ANCHOR: The highest file number for this block is 4371.
    # We start the counter at 4372 because we decrement *before* assigning.
    current_file_number = 4372

    # Iterate FORWARDS from q=1 to q=375, assigning file numbers from the TOP DOWN.
    for q in range(1, 376):
        if q in anomalous_unstarred_only:
            # This question has only ONE unstarred file.
            current_file_number -= 1
            file_map[q] = [current_file_number]
        else:
            # This is a normal question with TWO files (starred & unstarred).
            current_file_number -= 2
            starred = current_file_number
            unstarred = starred + 1
            file_map[q] = [starred, unstarred]

    # --- Step 2: Use the generated map to find the requested files ---
    
    files = []
    for q in question_numbers:
        if 1 <= q <= 375:
            # Look up the correctly calculated file numbers from our map
            if q in file_map:
                files.extend(file_map[q])
        
        elif 376 <= q <= 4000:
            # This logic remains unchanged
            file_num = 4001 - q
            files.append(file_num)
            
        else:
            # Question number outside known range
            raise ValueError(f"Question number {q} is out of valid range (1-4000).")

    return sorted(files)

def extract_ministry(content):
    """Extracts ministry/department from file content using robust pattern matching"""
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    
    # Priority 1: GOVERNMENT OF INDIA + next non-empty line
    for i, line in enumerate(lines):
        if "GOVERNMENT OF INDIA" in line.upper():
            # Look at next non-empty line
            for j in range(i+1, len(lines)):
                if lines[j].strip():
                    return lines[j].strip()
    
    # Priority 2: MINISTRY/DEPARTMENT pattern
    for line in lines:
        match = re.search(r'(MINISTRY|DEPARTMENT) OF .+', line, re.IGNORECASE)
        if match:
            ministry_str = match.group(0)
            # Standardize capitalization
            ministry_str = re.sub(r'ministry', 'Ministry', ministry_str, flags=re.IGNORECASE)
            ministry_str = re.sub(r'department', 'Department', ministry_str, flags=re.IGNORECASE)
            return ministry_str
    
    # Default if no match found
    return "Ministry of Power"

def parse_date_string(date_str):
    """Parses various date string formats into DD/MM/YYYY."""
    months = {
        'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4, 'MAY': 5, 'JUNE': 6,
        'JULY': 7, 'AUGUST': 8, 'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12
    }
    date_str = date_str.upper()

    # Handle formats like "THE 18TH MARCH, 2025" or "18TH MARCH, 2025"
    match = re.search(r'(\d{1,2})[A-Z]*\s+([A-Z]+)\s*,\s*(\d{4})', date_str)
    if match:
        day, month_str, year = match.groups()
        month = months.get(month_str, months.get(month_str[:3], 1))
        return f"{int(day):02d}/{month:02d}/{year}"

    # Handle formats like "TUESDAY, MARCH 18, 2025" or "MARCH 18, 2025"
    match = re.search(r'(?:[A-Z]+,\s*)?([A-Z]+)\s+(\d{1,2}),\s*(\d{4})', date_str)
    if match:
        month_str, day, year = match.groups()
        month = months.get(month_str, months.get(month_str[:3], 1))
        return f"{int(day):02d}/{month:02d}/{year}"

    # Handle "18.03.2025" format
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{int(day):02d}/{int(month):02d}/{year}"

    # Handle "18/03/2025" format
    match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', date_str)
    if match:
        # Pad with zeros if needed, e.g., 1/1/2025 -> 01/01/2025
        parts = match.group(1).split('/')
        return f"{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}"

    # Handle formats like "TUESDAY, THE 18TH MARCH, 2025"
    match = re.search(r'[A-Z]+,\s*THE\s+(\d{1,2})[A-Z]+\s+([A-Z]+),\s*(\d{4})', date_str)
    if match:
        day, month_str, year = match.groups()
        month = months.get(month_str, months.get(month_str[:3], 1))
        return f"{int(day):02d}/{month:02d}/{year}"

    return date_str.strip()

def extract_answer_parts(answer_text):
    """Extracts parts of an answer marked with (a), (b), etc."""
    # pattern = r'\(([a-z])\)(?:\s*&\s*\(([a-z])\))?\s*:|\(([a-z])\)\s*to\s*\(([a-z])\)\s*:'
    pattern = r'(?:[Aa]ns)?\s*\(([a-z])\)(?:\s*&\s*(?:[Aa]ns)?\s*\(([a-z])\))?\s*:?|(?:[Aa]ns)?\s*\(([a-z])\)\s*to\s*(?:[Aa]ns)?\s*\(([a-z])\)\s*:?'
    parts = []
    matches = list(re.finditer(pattern, answer_text))
    if not matches:
        return [{'markers': ['all'], 'text': answer_text.strip()}]

    for i, match in enumerate(matches):
        markers = [m for m in match.groups() if m]
        start_pos = match.end()
        end_pos = matches[i+1].start() if i < len(matches)-1 else len(answer_text)
        text = answer_text[start_pos:end_pos].strip()
        text = re.sub(r'\s+', ' ', text)
        parts.append({'markers': markers, 'text': text})
    return parts

def process_file_content(content):
    """Extracts all relevant fields from the text content of a file."""
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    # Initialize variables with default values
    ministry = extract_ministry(content)  # Using the improved ministry extraction
    question_no, question_title, member_name = "N/A", "N/A", "N/A"
    question_text = "N/A"
    answered_date, answered_by = "N/A", "N/A"
    answer_text_content = ""

    # --- Extraction Logic using Regex ---

    # Question Number
    
    for line in lines:
        # match = re.search(r'(?:STARRED|UNSTARRED)?\s*QUESTION\s*NO\.?\s*(\*?\d+)', line, re.IGNORECASE)
        match = re.search(r'(?:STARRED|UNSTARRED)?\s*QUESTION\s*NO\s*[^0-9\n]*(\d+)', line, re.IGNORECASE)
        if match:
            question_no = match.group(1).replace('*', '').strip()
            break

    # Answered Date
    date_line_index = -1
    for idx, line in enumerate(lines):
        if "ANSWERED ON" in line.upper() or "ANSWER ON" in line.upper():
            date_part = line.split("ANSWERED ON")[-1].strip()
            answered_date = parse_date_string(date_part)
            date_line_index = idx
            break

    # Question Title
    if date_line_index != -1 and date_line_index + 1 < len(lines):
        question_title = lines[date_line_index + 1]


    # # Question Text
    # q_start, q_end = -1, -1
    # for i, line in enumerate(lines):
    #     print(i ," -> ",line)
    #     normalized_line = re.sub(r'\s+', ' ', line.lower())
    #     # Find the *first* line that starts the question phrase
    #     if "will the minister" in normalized_line and q_start == -1: 
    #         q_start = i
        
    #     answer_check_line = re.sub(r'\s+', '', line.lower())
    #     # Find the "ANSWER" line *after* the question has started
    #     if q_start != -1 and "answer" in answer_check_line:
    #         q_end = i
    #         break
    
                
    # # --- This logic handles both normal and question-only files ---
    # if q_start != -1:
    #     # We found the start of the question.
        
    #     if q_end != -1:
    #         # Case 1: Normal - "ANSWER" was found.
    #         question_text_lines = lines[q_start:q_end]
    #     else:
    #         # Case 2: Question-only file - "ANSWER" was NOT found.
    #         # Take all lines from the start of the question to the end.
    #         question_text_lines = lines[q_start:]

    #     # Join and clean the text
    #     question_text = ' '.join(question_text_lines).strip()
    #     question_text = re.sub(r'\s+', ' ', question_text)
    #     # Remove any trailing junk
    #     question_text = question_text.split('*****')[0].strip()

    # Question Text and Answer Block Start
    q_start = -1
    answer_block_start_index = -1 # This will be the index of "ANSWER" or "MINISTER..."
    
    for i, line in enumerate(lines):
        # Normalize line for checking
        normalized_line = re.sub(r'\s+', ' ', line.lower())
        
        # Find q_start (only once)
        if q_start == -1 and ("will the minister" in normalized_line or "wil the minister" in normalized_line): 
            q_start = i
            
        # Find start of answer block (which is the end of the question)
        if q_start != -1 and answer_block_start_index == -1:
            # Check for "ANSWER"
            answer_check_line = re.sub(r'\s+', '', line.lower())
            if answer_check_line == "answer":
                answer_block_start_index = i
                break # Found it, stop
                
            # Check for Minister Title
            if line.upper().startswith("MINISTER") or line.upper().startswith("THE MINISTER"):
                answer_block_start_index = i
                break # Found it, stop

    # --- Process Question Text ---
    if q_start != -1:
        if answer_block_start_index != -1:
            # Normal case: Found start of answer block
            question_text_lines = lines[q_start:answer_block_start_index]
        else:
            # Question-only file case
            question_text_lines = lines[q_start:]
        
        question_text = ' '.join(question_text_lines).strip()
        question_text = re.sub(r'\s+', ' ', question_text)
        question_text = question_text.split('*****')[0].strip()

    

# Questioned By
    member_names = []
    KNOWN_PREFIXES = ['SHRI', 'SMT', 'DR', 'THIRU', 'MR', 'PROF', 'MS', 'COM'] 

    if q_start != -1: # We must have found the "Will the Minister..." line
        # --- PRIMARY LOGIC ---
        # Start from the line *right before* the question and loop backwards
        for i in range(q_start - 1, -1, -1):
            line = lines[i].strip().strip(':')
            line_upper = line.upper()

            # Check if this line starts with a known prefix
            if any(line_upper.startswith(prefix) for prefix in KNOWN_PREFIXES):
                member_names.append(line)
            
            # If we hit a non-empty, non-member line (like the title), stop.
            elif line: 
                break
        
        if member_names:
            # We found them bottom-to-top, so reverse the list
            member_names.reverse()
            member_name = ', '.join(member_names)

    # --- FALLBACK LOGIC (NOW CONSTRAINED) ---
    if member_name == "N/A" and question_no != "N/A":
        # The backwards logic failed.
        # Try searching FORWARDS, but *only up to the question start* (q_start).
        
        # Define the search range: from the start of the file up to the question
        search_range_end = q_start if q_start != -1 else len(lines) 
        
        for i in range(search_range_end):
            line = lines[i]
            if re.search(r'\b' + re.escape(question_no) + r'\b', line):
                line_upper = line.upper()
                if any(prefix in line_upper for prefix in KNOWN_PREFIXES):
                    # Found the line. Extract name.
                    potential_name = re.sub(r'^.*?' + re.escape(question_no) + r'[.:]*\s*', '', line).strip(': ')
                    potential_name_upper = potential_name.upper()
                    if any(potential_name_upper.startswith(prefix) for prefix in KNOWN_PREFIXES):
                         member_names.append(potential_name.strip(':'))
                         
                         # Check subsequent lines, but still only up to the question
                         for j in range(i + 1, search_range_end): 
                             next_line = lines[j].strip().strip(':')
                             next_line_upper = next_line.upper()
                             if any(next_line_upper.startswith(prefix) for prefix in KNOWN_PREFIXES):
                                 member_names.append(next_line)
                             elif next_line:
                                 continue # Skip junk lines
                             else:
                                 break
                         
                         member_name = ', '.join(member_names)
                         break # Found, so stop the main loop    # Question Text
    

    # Answer Text, Answered By
    # ans_start = -1
    # for i, line in enumerate(lines):
    #     normalized_line = re.sub(r'\s+', '', line.lower())
    #     # print(i," -> ",line)
    #     if normalized_line == "answer":
    #         ans_start = i
    #         break

    # # print(ans_start)
    # name_line_index = -1 # Index of the line containing the minister's name
    # answer_text_start_index = ans_start + 1 # Default start for answer text

    # if ans_start != -1:
    #     # --- Answered By ---
    #     # Iterate lines *after* "ANSWER" to find the minister's name
    #     for i, line in enumerate(lines[ans_start + 1:], start=ans_start + 1):
    #         print(i," -> ",line)

    #         match = re.search(r'[\[\(\{]\s*(?:(SHRI|SMT\.?|SHRIMATI|DR\.?|SUSHRI)\s+)?([A-Z\s.-]+)[\)\]\}]', line, re.IGNORECASE)
            
    #         if match:
    #             # --- MODIFIED LOGIC ---
    #             title_str = match.group(1) # This is the prefix (e.g., "DR.") or None
    #             name_str = match.group(2).strip()  # This is the name (e.g., "SUKANTA MAJUMDAR")
                
    #             # Capitalize the name part
    #             name = ' '.join(word.capitalize() for word in name_str.split())
                
    #             if title_str:
    #                 # A title was found, process it
    #                 title = title_str.title().replace('.', '')
    #                 if "Shrimati" in title: title = "Smt"
    #                 if "Dr" in title: title = "Dr"
    #                 if "Sushri" in title: title = "Sushri" # Handle new prefix
    #                 answered_by = f"{title}. {name}"
    #             else:
    #                 # No title was found, just use the capitalized name
    #                 answered_by = name 
                
    #             name_line_index = i
    #             answer_text_start_index = name_line_index + 1 # Answer text starts *after* this line
    #             break # Found it, stop searching

    #     # --- Answer ---
    #     # This part remains the same, but now it gets the correct start index
    #     answer_lines = lines[answer_text_start_index:]
    #     answer_text_content = '\n'.join(line for line in answer_lines if line.strip() and line != '*****').strip()
                
    #     # Answer
    #     answer_lines = lines[answer_text_start_index:]
    #     # Clean up minister name from answer start if present
    #     # answer_text_content = '\n'.join(line for line in answer_lines if line.strip() and line != '*****').strip()
    #     answer_text_content = '\n'.join(line for line in answer_lines if line.strip() and line != '*****').strip()

# Answer Text & Answered By
    answered_by = "N/A"
    answer_text_content = ""
    
    if answer_block_start_index != -1:
        # We have a block of lines to search, starting from the anchor
        answer_block_lines = lines[answer_block_start_index:]
        
        # --- Find Answered By (within the answer block) ---
        answer_text_start_index_relative = 0 # Default start for answer
        
        for i, line in enumerate(answer_block_lines):
            # print(i," -> ",line)
            # --- YOUR NEW CHECK ---
            # If the line looks like the start of the answer (e.g., "(a)", "a)"),
            # stop looking for the minister's name.
            clean_line = line.strip().lower()
            if re.search(r'^\s*(?:[Aa]ns)?\s*(?:\([a-z]\)|[a-z]\))', clean_line):
                break # Stop the loop
            # --- END NEW CHECK ---

            # Find ALL name-like patterns on this line
            matches = re.findall(r'[\[\(\{]\s*(?:(SHRI|SMT\.?|SHRIMATI|DR\.?|SUSHRI)\s+)?([A-Z\s.-]+)[\)\]\}]', line, re.IGNORECASE)
            # print(matches)
            if matches:
                # We only care about the *last* match on the line
                last_match = matches[-1]
                
                # --- This is a *potential* name. Keep overwriting ---
                title_str = last_match[0] # Group 1 (prefix)
                name_str = last_match[1].strip()  # Group 2 (name)
                
                name = ' '.join(word.capitalize() for word in name_str.split())
                
                if title_str:
                    title = title_str.title().replace('.', '')
                    if "Shrimati" in title: title = "Smt"
                    if "Dr" in title: title = "Dr"
                    if "Sushri" in title: title = "Sushri"
                    answered_by = f"{title}. {name}"
                else:
                    answered_by = name 
                
                # We found a name on this line, so the answer must start *after* this line
                answer_text_start_index_relative = i + 1

        # --- Find Answer Text ---
        # The loop is finished. answer_text_start_index_relative is now set
        # to the line *after* the LAST name we found.
        
        # Filter out "ANSWER" and "MINISTER" lines from the real answer lines
        final_answer_lines = []
        for line in answer_block_lines[answer_text_start_index_relative:]:
            # Check for "ANSWER"
            answer_check_line = re.sub(r'\s+', '', line.lower())
            if answer_check_line == "answer":
                continue # Skip the "ANSWER" line
            
            final_answer_lines.append(line)

        answer_text_content = '\n'.join(line for line in final_answer_lines if line.strip() and line != '*****').strip()

    # Process answer parts for final formatting
    parts = extract_answer_parts(answer_text_content)
    final_answer_str = ""
    if len(parts) == 1 and 'all' in parts[0]['markers']:
        final_answer_str = re.sub(r'\s+', ' ', parts[0]['text']).strip()
    else:
        for part in parts:
            markers_str = " & ".join([f"({m})" for m in part['markers']])
            final_answer_str += f"{markers_str} {part['text']} "

    final_answer = final_answer_str.strip() if final_answer_str.strip() else answer_text_content

    return {
        "Ministry": ministry,
        "Question No": question_no,
        "Question Title": question_title,
        "Questioned By": member_name,
        "Question": question_text,
        "Answered Date": answered_date,
        "Answered By": answered_by,
        "Answer": final_answer
    }

def read_pdf_or_txt(filepath):
    """Reads either PDF or TXT file and returns plain text content."""
    if filepath.lower().endswith('.pdf'):
        try:
            text = extract_text(filepath)
            return text
        except Exception as e:
            raise RuntimeError(f"PDF text extraction failed for {filepath}: {e}")
    else:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()


def main():
    # Configuration
    directory = r"C:\Users\nishn\OneDrive\Desktop\BTP\BTP\RTI\pdfs"
    
    output_file = os.path.join(directory, "processed_results_all_files.json")

    # Collect all .pdf files in the folder
    all_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    print(f"Found {len(all_files)} PDF files to process.\n")


    # specific_filename = "page10_file50.pdf"  # <--- CHANGE THIS    
    # output_filename = f"processed_result_{specific_filename}.json"
    # output_file = os.path.join(directory, output_filename)

    # # 3. Create a list with just that one file
    # all_files = [specific_filename] 
    # print(f"Processing 1 specific file: {specific_filename}\n")

    results = []

    cnt = 0
    # Process each file
    for filename in sorted(all_files):
        filepath = os.path.join(directory, filename)
        try:
            content = read_pdf_or_txt(filepath)
            result = process_file_content(content)
            result["file"] = filename
            results.append(result)
            print(f"✅ Processed {filename}")

            
        except Exception as e:
            print(f"❌ ERROR processing {filename}: {e}")
            results.append({
                "file": filename,
                "status": "Error",
                "detail": str(e)
            })
        cnt+=1
        # if cnt > 100:
        #     break
    
    # Save results
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(results, outfile, indent=4, ensure_ascii=False)
    
    print(f"\n✅ Processing complete. total processed = cnt. Results saved to: {output_file}")

if __name__ == "__main__":
    main()