"""General purpose utility functions"""

import re
from typing import List, Optional


def find_unescaped(text: str, char: str) -> Optional[int]:
    """
    Find occurrence of an unescaped character.

    @param text: String
    @param char: Character to find
    @return: Index of first match, None if no match

    Examples:
    >>> find_unescaped('BEGIN:VCARD', ':')
    5
    >>> find_unescaped('foo\\\\,bar,baz', ',')
    8
    >>> find_unescaped('foo\\\\\\\\,bar,baz', ',')
    5
    >>> find_unescaped('foo,bar,baz', ':')
    >>> find_unescaped('foo\\\\,bar\\\\,baz', ',')
    """
    escaped_char = re.escape(char)
    unescaped_regex = f"(?<!\\\\)(?:\\\\\\\\)*({escaped_char})"
    regex = re.compile(unescaped_regex)

    char_match = regex.search(text)

    if char_match is None:
        return None
    return char_match.start(1)


def split_unescaped(text: str, separator: str) -> List[str]:
    """
    Find strings separated by an unescaped character.

    @param text: String
    @param separator: Separator
    @return: List of strings between separators, excluding the separator
    """
    result = []
    while True:
        index = find_unescaped(text, separator)
        if index is not None:
            result.append(text[:index])
            text = text[index + 1 :]
        else:
            result.append(text)
            return result
