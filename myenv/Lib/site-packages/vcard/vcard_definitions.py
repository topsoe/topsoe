"""vCard v3.0 (RFC 2426) definitions and message strings"""
import re
from string import ascii_letters, digits

# Literals, RFC 2426 pages 27, 28
NEWLINE_CHARACTERS = "\r\n"
DOUBLE_QUOTE_CHARACTER = '"'
SPACE_CHARACTER = " "
SPACE_CHARACTERS = f"{SPACE_CHARACTER}\t"
NON_ASCII_CHARACTERS = (
    "\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f"
    "\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f"
    "\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf"
    "\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf"
    "\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf"
    "\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf"
    "\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef"
    "\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"
)

SAFE_PUNCTUATION_CHARACTERS = "!#$%&'()*+-./<=>?@[]^_`{|}~"
SAFE_CHARACTERS = (
    f"{SPACE_CHARACTERS}{SAFE_PUNCTUATION_CHARACTERS}{digits}{ascii_letters}{NON_ASCII_CHARACTERS}"
)
SAFE_REGEX_CHARACTERS = re.escape(SAFE_CHARACTERS)
QUOTE_SAFE_CHARACTERS = f"{SAFE_CHARACTERS},:;"
QUOTE_SAFE_REGEX_CHARACTERS = re.escape(QUOTE_SAFE_CHARACTERS)
REGEX_VALUE_CHARACTERS = re.escape(f"{QUOTE_SAFE_CHARACTERS}\\{DOUBLE_QUOTE_CHARACTER}")
REGEX_ESCAPED_CHARACTERS = re.escape("\\;,nN")

# Known property names (RFC 2426 page 4)
MANDATORY_PROPERTIES = ["BEGIN", "END", "FN", "N", "VERSION"]
PREDEFINED_PROPERTIES = ["BEGIN", "END", "NAME", "PROFILE", "SOURCE"]
OTHER_PROPERTIES = [
    "ADR",
    "AGENT",
    "BDAY",
    "CATEGORIES",
    "CLASS",
    "EMAIL",
    "GEO",
    "KEY",
    "LABEL",
    "LOGO",
    "MAILER",
    "NICKNAME",
    "NOTE",
    "ORG",
    "PHOTO",
    "PRODID",
    "REV",
    "ROLE",
    "SORT-STRING",
    "SOUND",
    "TEL",
    "TITLE",
    "TZ",
    "UID",
    "URL",
]
ALL_PROPERTIES = list(set(MANDATORY_PROPERTIES + PREDEFINED_PROPERTIES + OTHER_PROPERTIES))

# IDs for group, name, iana-token, x-name, param-name (RFC 2426 page 29)
ID_CHARACTERS = f"{ascii_letters}{digits}-"
ID_REGEX_CHARACTERS = re.escape(ID_CHARACTERS)

VCARD_LINE_MAX_LENGTH = 75
"""RFC 2426 page 6"""

VCARD_LINE_MAX_LENGTH_RAW = VCARD_LINE_MAX_LENGTH + len(NEWLINE_CHARACTERS)
"""Including line ending"""
