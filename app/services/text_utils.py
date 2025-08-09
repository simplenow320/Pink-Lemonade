import re

def md_to_plain(md: str) -> str:
    if not md:
        return ""
    s = md
    # headings and bold/italics
    s = re.sub(r'[#*_`]+', '', s)
    # links [text](url) -> text (url)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', s)
    # bullets -> dash
    s = re.sub(r'^\s*[-•]\s*', '- ', s, flags=re.MULTILINE)
    # collapse extra spaces
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()