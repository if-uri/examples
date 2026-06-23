import os
import email
import datetime
import json
import mailbox
import re
from email.utils import parsedate_to_datetime

def get_account_mapping(profile_dir):
    prefs_path = os.path.join(profile_dir, "prefs.js")
    if not os.path.exists(prefs_path):
        return {}
        
    dir_prefs = {}
    name_prefs = {}
    
    with open(prefs_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m_dir = re.search(r'user_pref\("mail\.server\.(server\d+)\.directory",\s*"(.*?)"\);', line)
            if m_dir:
                server_id, dir_path = m_dir.group(1), m_dir.group(2)
                dir_prefs[server_id] = os.path.basename(dir_path)
                continue
                
            m_name = re.search(r'user_pref\("mail\.server\.(server\d+)\.name",\s*"(.*?)"\);', line)
            if m_name:
                server_id, name = m_name.group(1), m_name.group(2)
                name_prefs[server_id] = name
                continue
                
    mapping = {}
    for server_id, dir_name in dir_prefs.items():
        if server_id in name_prefs:
            mapping[dir_name] = name_prefs[server_id]
            
    return mapping

def process_message_lines(lines, date_str, msg_date, subject_str, search_terms, downloads_dir, account):
    msg_str = "".join(lines)
    msg = email.message_from_string(msg_str)
    
    subject = msg.get("Subject", "")
    try:
        decoded_subject = str(email.header.make_header(email.header.decode_header(subject)))
    except Exception:
        decoded_subject = subject
        
    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disp:
                try:
                    body_text += part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                except Exception:
                    pass
    else:
        if msg.get_content_type() == "text/plain":
            try:
                body_text = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')
            except Exception:
                pass
                
    is_invoice = False
    subj_lower = decoded_subject.lower()
    body_lower = body_text.lower()
    
    if any(term in subj_lower for term in search_terms):
        is_invoice = True
        
    attachments = []
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
            
        filename = part.get_filename()
        if filename:
            try:
                decoded_filename = str(email.header.make_header(email.header.decode_header(filename)))
            except Exception:
                decoded_filename = filename
                
            attachments.append((decoded_filename, part))
            if any(term in decoded_filename.lower() for term in search_terms) or decoded_filename.lower().endswith(".pdf"):
                is_invoice = True
                
    saved_files = []
    if is_invoice:
        month_str = msg_date.strftime("%Y-%m")
        # Sanitize account name for directory path
        safe_account = "".join(c for c in account if c.isalnum() or c in "@._- ").strip()
        if not safe_account:
            safe_account = "Unknown"
        target_dir = os.path.join(downloads_dir, month_str, safe_account)
        os.makedirs(target_dir, exist_ok=True)
        
        for fname, part in attachments:
            safe_fname = "".join(c for c in fname if c.isalnum() or c in "._- ").strip()
            if not safe_fname:
                safe_fname = "attachment"
            dest_path = os.path.join(target_dir, safe_fname)
            base, ext = os.path.splitext(safe_fname)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                counter += 1
                
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    with open(dest_path, "wb") as out_f:
                        out_f.write(payload)
                    saved_files.append(os.path.basename(dest_path))
            except Exception:
                pass
                
        if not saved_files:
            safe_subject = "".join(c for c in decoded_subject if c.isalnum() or c in "._- ").strip()[:50]
            if not safe_subject:
                safe_subject = "mail"
            dest_path = os.path.join(target_dir, f"{safe_subject}.txt")
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(target_dir, f"{safe_subject}_{counter}.txt")
                counter += 1
            try:
                with open(dest_path, "w", encoding="utf-8") as out_f:
                    out_f.write(f"Subject: {decoded_subject}\nDate: {date_str}\n\n{body_text}")
                saved_files.append(os.path.basename(dest_path))
            except Exception:
                pass
                
    return saved_files

def parse_mbox_fast(mbox_path, start_date, end_date, search_terms, downloads_dir, account):
    saved_count = 0
    details = []
    
    with open(mbox_path, "r", encoding="utf-8", errors="replace") as f:
        msg_lines = []
        in_header = True
        msg_date = None
        date_str = ""
        subject_str = ""
        is_in_date_range = False
        
        for line in f:
            if line.startswith("From "):
                # New message starts. Process previous message if it was in date range
                if msg_lines and is_in_date_range:
                    saved = process_message_lines(msg_lines, date_str, msg_date, subject_str, search_terms, downloads_dir, account)
                    if saved:
                        saved_count += len(saved)
                        details.append({
                            "date": date_str,
                            "subject": subject_str,
                            "mailbox": os.path.basename(mbox_path),
                            "saved": saved
                        })
                
                # Reset for new message
                msg_lines = [line]
                in_header = True
                msg_date = None
                date_str = ""
                subject_str = ""
                is_in_date_range = False
            else:
                msg_lines.append(line)
                if in_header:
                    if line.strip() == "":
                        in_header = False
                        # Check date
                        if date_str:
                            try:
                                msg_date = parsedate_to_datetime(date_str)
                                if start_date <= msg_date < end_date:
                                    is_in_date_range = True
                            except Exception:
                                pass
                    else:
                        line_lower = line.lower()
                        if line_lower.startswith("date:"):
                            date_str = line[5:].strip()
                        elif line_lower.startswith("subject:"):
                            subject_str = line[8:].strip()
                        
        # Don't forget the last message
        if msg_lines and is_in_date_range:
            saved = process_message_lines(msg_lines, date_str, msg_date, subject_str, search_terms, downloads_dir, account)
            if saved:
                saved_count += len(saved)
                details.append({
                    "date": date_str,
                    "subject": subject_str,
                    "mailbox": os.path.basename(mbox_path),
                    "saved": saved
                })
                
    return saved_count, details

def run_extraction():
    profile_dir = os.path.expanduser("~/.var/app/org.mozilla.Thunderbird/.thunderbird/ax819b7g.default-release")
    downloads_dir = os.path.expanduser("~/Downloads")
    
    start_date = datetime.datetime(2026, 3, 1, tzinfo=datetime.timezone.utc)
    end_date = datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc)
    
    total_saved = 0
    scanned_mboxs = 0
    details = []
    
    # Get account mapping from prefs.js
    account_mapping = get_account_mapping(profile_dir)
    
    # Search terms (case-insensitive)
    search_terms = ["faktura", "invoice", "fv", "rachunek", "bill", "płatność", "opłata", "faktury"]
    
    for root_dir in ["ImapMail", "Mail"]:
        full_root = os.path.join(profile_dir, root_dir)
        if not os.path.isdir(full_root):
            continue
            
        for root, dirs, files in os.walk(full_root):
            for file in files:
                if file.endswith((".msf", ".ini", ".dat", ".json", ".txt", ".html", ".sqlite")):
                    continue
                mbox_path = os.path.join(root, file)
                if os.path.getsize(mbox_path) == 0:
                    continue
                    
                # verify it is a mailbox file (starts with "From ")
                try:
                    with open(mbox_path, "rb") as f:
                        start = f.read(5)
                        if start != b"From ":
                            continue
                except Exception:
                    continue
                
                # Determine account directory name
                relative_path = os.path.relpath(mbox_path, profile_dir)
                parts = relative_path.split(os.sep)
                dir_name = parts[1] if len(parts) >= 2 else "Unknown"
                
                # Map directory name to actual account name (e.g. email address)
                account = account_mapping.get(dir_name, dir_name)
                
                scanned_mboxs += 1
                try:
                    saved_count, mbox_details = parse_mbox_fast(mbox_path, start_date, end_date, search_terms, downloads_dir, account)
                    total_saved += saved_count
                    details.extend(mbox_details)
                except Exception as e:
                    pass
                    
    return {
        "ok": True,
        "scanned_mboxs": scanned_mboxs,
        "saved_count": total_saved,
        "details": details
    }

if __name__ == "__main__":
    res = run_extraction()
    print(json.dumps(res, indent=2))
