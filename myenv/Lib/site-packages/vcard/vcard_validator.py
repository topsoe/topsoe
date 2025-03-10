import codecs
import re
from contextlib import contextmanager
from sys import stdin
from typing import Iterator, List, MutableMapping, Optional, Sequence, Set, TextIO, TypedDict
from warnings import warn

from . import vcard_utils, vcard_validators
from .vcard_definitions import (
    ALL_PROPERTIES,
    ID_REGEX_CHARACTERS,
    MANDATORY_PROPERTIES,
    NEWLINE_CHARACTERS,
    QUOTE_SAFE_REGEX_CHARACTERS,
    REGEX_VALUE_CHARACTERS,
    SAFE_REGEX_CHARACTERS,
    SPACE_CHARACTER,
    VCARD_LINE_MAX_LENGTH_RAW,
)
from .vcard_errors import (
    NOTE_CONTINUATION_AT_START,
    NOTE_DOT_AT_LINE_START,
    NOTE_EMPTY_VCARD,
    NOTE_INVALID_LINE_SEPARATOR,
    NOTE_INVALID_PARAMETER_NAME,
    NOTE_INVALID_PROPERTY_NAME,
    NOTE_INVALID_SUB_VALUE,
    NOTE_INVALID_VALUE,
    NOTE_MISMATCH_GROUP,
    NOTE_MISSING_GROUP,
    NOTE_MISSING_PARAM_VALUE,
    NOTE_MISSING_PROPERTY,
    NOTE_MISSING_VALUE_STRING,
    VCardError,
    VCardItemCountError,
    VCardLineError,
    VCardNameError,
    VCardValueError,
)
from .vcard_property import VcardProperty

VCARD_PROPERTY_PARAMETER = TypedDict("VCARD_PROPERTY_PARAMETER", {"name": str, "values": Set[str]})


class VcardValidator:  # pylint: disable=too-few-public-methods
    def __init__(self, path: str, verbose: bool):
        self.path = path
        self.verbose = verbose
        self.result = self.validate()

    def validate(self) -> str:
        return validate_file(self.path, self.verbose)


@contextmanager
def get_file_pointer(filename: str) -> Iterator[TextIO]:
    if filename == "-":
        yield stdin
    else:
        with codecs.open(filename, "r", "utf-8") as file_pointer:
            yield file_pointer


def validate_file(filename: str, verbose: bool) -> str:
    """
    Create object for each vCard in a file, and show the error output.

    @param filename: Path to file
    @param verbose: Verbose mode
    @return: Debugging output from creating vCards
    """
    with get_file_pointer(filename) as file_pointer:
        contents = file_pointer.read().splitlines(True)

    vcard_text = ""
    result = ""
    try:
        for index, line in enumerate(contents):
            vcard_text += line

            if line == f"END:VCARD{NEWLINE_CHARACTERS}":
                validate_vcard_text(vcard_text, filename, index, verbose)
                vcard_text = ""

    except VCardError as error:
        result += str(error)

    if vcard_text != "" and result == "":
        line_count = len(vcard_text.splitlines(False))
        result += f"Could not process entire {filename} - {line_count} lines remain"

    return result


def validate_vcard_text(vcard_text: str, filename: str, line_index: int, verbose: bool) -> None:
    try:
        vcard = VCard(vcard_text, filename)
        if verbose:
            print(vcard)
    except VCardError as error:
        error.context["File"] = filename
        error.context["File line"] = line_index
        raise


class VCard:  # pylint: disable=too-few-public-methods
    """Container for structured and unstructured vCard contents."""

    def __init__(self, text: str, filename: Optional[str] = None):
        """
        Create vCard object from text string. Includes text (the entire
        unprocessed vCard), group (optional prefix on each line) and
        properties.

        @param text: String containing a single vCard
        """
        if text == "" or text is None:
            raise VCardError(NOTE_EMPTY_VCARD, {"vCard line": 1, "File line": 1})

        self.text = text

        self.filename = filename

        lines = unfold_vcard_lines(self.text.splitlines(True))

        # Groups
        self.group = get_vcard_group(lines)
        lines = remove_vcard_groups(lines, self.group)

        # Properties
        self.properties = get_vcard_properties(lines)

    def __str__(self) -> str:
        return self.text


def unfold_vcard_lines(lines: Sequence[str]) -> List[str]:
    """
    Un-split lines in vCard, warning about short lines. RFC 2426 page 8.

    @param lines: List of potentially folded vCard lines
    @return: List of lines, one per property
    """
    property_lines: List[str] = []
    for index, line in enumerate(lines):
        if not line.endswith(NEWLINE_CHARACTERS):
            raise VCardLineError(NOTE_INVALID_LINE_SEPARATOR, {"File line": index + 1})

        if len(line) > VCARD_LINE_MAX_LENGTH_RAW:
            warn(f"Long line in vCard: {line}")

        if line.startswith(" "):
            if index == 0:
                raise VCardLineError(NOTE_CONTINUATION_AT_START, {"File line": index + 1})
            if len(lines[index - 1]) < VCARD_LINE_MAX_LENGTH_RAW:
                warn(f"Short folded line at line {index - 1}")
            elif line == f"{SPACE_CHARACTER}{NEWLINE_CHARACTERS}":
                warn(f"Empty folded line at line {index}")
            property_lines[-1] = property_lines[-1][: -len(NEWLINE_CHARACTERS)] + line[1:]
        else:
            property_lines.append(line)

    return property_lines


def get_vcard_group(lines: List[str]) -> Optional[str]:
    """
    Get & validate group. RFC 2426 pages 28, 29.

    @param lines: List of unfolded vCard lines
    @return: Group name if one exists, None otherwise
    """
    group = None

    group_re = re.compile(f"^([{ID_REGEX_CHARACTERS}]*)\\.")

    group_match = group_re.match(lines[0])
    if group_match is not None:
        group = group_match.group(1)

        # Validate
        if len(group) == 0:
            raise VCardLineError(NOTE_DOT_AT_LINE_START, {})

        for index, line in enumerate(lines):
            next_match = group_re.match(line)
            if not next_match:
                raise VCardLineError(NOTE_MISSING_GROUP, {"File line": index + 1})
            if next_match.group(1) != group:
                raise VCardNameError(
                    f"{NOTE_MISMATCH_GROUP}: {next_match.group(1)} != {group}",
                    {"File line": index + 1},
                )
    else:
        # Make sure there are no groups elsewhere
        for index, line in enumerate(lines):
            next_match = group_re.match(line)
            if next_match:
                raise VCardNameError(
                    f"{NOTE_MISMATCH_GROUP}: {next_match.group(1)} != {group}",
                    {"File line": index + 1},
                )

    return group


def remove_vcard_groups(lines: List[str], group: Optional[str]) -> List[str]:
    """
    Remove groups from vCard. RFC 2426 pages 28, 29.

    @param lines: List of unfolded vCard lines
    @param group: Name of group
    @return: Lines without groups and dot separator
    """
    if group:
        for index, line in enumerate(lines):
            lines[index] = line[len(group) :]
    return lines


def get_vcard_properties(lines: List[str]) -> List[VcardProperty]:
    """
    Get the properties for each line. RFC 2426 pages 28, 29.

    @param lines: List of unfolded vCard lines
    @return: List of properties, for simplicity. AFAIK sequence doesn't matter
    and duplicates add no information, but ignoring this to make sure vCard
    output looks like the original.
    """
    properties = []
    for index, property_line in enumerate(lines):
        if property_line != NEWLINE_CHARACTERS:
            try:
                properties.append(get_vcard_property(property_line))
            except VCardError as error:
                error.context["vCard line"] = index
                raise

    for mandatory_property in MANDATORY_PROPERTIES:
        if mandatory_property not in [property_.name.upper() for property_ in properties]:
            raise VCardItemCountError(
                f"{NOTE_MISSING_PROPERTY}: {mandatory_property}", {"Property": mandatory_property}
            )

    return properties


def get_vcard_property(property_line: str) -> VcardProperty:
    """
    Get a single property.

    @param property_line: Single unfolded vCard line
    @return: Dictionary with name, parameters and values
    """
    property_parts = vcard_utils.split_unescaped(property_line, ":")
    if len(property_parts) < 2:
        raise VCardItemCountError(f"{NOTE_MISSING_VALUE_STRING}: {property_line}", {})
    if len(property_parts) > 2:
        # Merge - Colon doesn't have to be escaped in values
        property_parts[1] = ":".join(property_parts[1:])
        property_parts = property_parts[:2]
    property_string, values_string = property_parts  # pylint: disable=unbalanced-tuple-unpacking

    # Split property name and property parameters
    property_name_and_params = vcard_utils.split_unescaped(property_string, ";")

    property_name = property_name_and_params.pop(0)

    # String validation
    if not property_name.upper() in ALL_PROPERTIES and not re.match(
        f"^X-[{ID_REGEX_CHARACTERS}]+$", property_name, re.IGNORECASE
    ):
        raise VCardNameError(f"{NOTE_INVALID_PROPERTY_NAME}: {property_name}", {})

    try:
        property_values = get_vcard_property_values(values_string)
        property_ = VcardProperty(property_name, property_values)
        if len(property_name_and_params) != 0:
            property_.parameters = get_vcard_property_params(";".join(property_name_and_params))

        # Validate
        vcard_validators.validate_vcard_property(property_)
    except VCardError as error:
        # Add parameter name to error
        error.context["Property line"] = property_line
        raise

    return property_


def get_vcard_property_params(params_string: str) -> MutableMapping[str, Set[str]]:
    """
    Get the parameters and their values. RFC 2426 page 28.

    @param params_string: Part of a vCard line between the first semicolon
    and the first colon.
    @return: Dictionary of parameters. Assumes that
    TYPE=WORK;TYPE=WORK,VOICE === TYPE=VOICE,WORK === TYPE=VOICE;TYPE=WORK.
    """
    params: MutableMapping[str, Set[str]] = {}
    if not params_string:
        return params

    for parameter_string in vcard_utils.split_unescaped(params_string, ";"):
        parameter = get_vcard_property_parameter(parameter_string)
        param_name = parameter["name"].upper()  # To be able to merge TYPE & type
        if param_name not in params:
            params[param_name] = parameter["values"]
        else:
            # Merge
            params[param_name] = params[param_name].union(parameter["values"])

    return params


def get_vcard_property_values(values_string: str) -> List[List[str]]:
    """
    Get the property values.

    @param values_string: Multiple value string
    @return: List of values (RFC 2426 page 12)
    """
    values = []

    # Strip line ending
    values_string = values_string[: -len(NEWLINE_CHARACTERS)]

    sub_value_strings = vcard_utils.split_unescaped(values_string, ";")
    for sub in sub_value_strings:
        values.append(get_vcard_property_sub_values(sub))

    return values


def get_vcard_property_parameter(param_string: str) -> VCARD_PROPERTY_PARAMETER:
    """
    Get the parameter name and value(s). RFC 2426 page 29.

    @param param_string: Single parameter and values
    @return: Dictionary with a parameter name and values
    """
    try:
        (  # pylint: disable=unbalanced-tuple-unpacking
            param_name,
            values_string,
        ) = vcard_utils.split_unescaped(param_string, "=")
    except ValueError as error:
        raise VCardItemCountError(f"{NOTE_MISSING_PARAM_VALUE}: {str(error)}", {}) from error

    values = get_vcard_property_param_values(values_string)

    # Validate
    if not re.match(f"^[{ID_REGEX_CHARACTERS}]+$", param_name):
        raise VCardNameError(f"{NOTE_INVALID_PARAMETER_NAME}: {param_name}", {})

    return {"name": param_name, "values": values}


def get_vcard_property_sub_values(value_string: str) -> List[str]:
    """
    Get the parts of the value.

    @param value_string: Single value string
    @return: List of values (RFC 2426 page 9)
    """
    sub_values = vcard_utils.split_unescaped(value_string, ",")

    # Validate string
    for sub_value in sub_values:
        if not re.match(f"^[{REGEX_VALUE_CHARACTERS}]*$", sub_value):
            raise VCardValueError(f"{NOTE_INVALID_SUB_VALUE}: {sub_value}", {})

    return sub_values


def get_vcard_property_param_values(values_string: str) -> Set[str]:
    """
    Get the parameter values. RFC 2426 page 29.

    @param values_string: Comma separated values
    @return: Set of values. Assumes that sequence doesn't matter and that
    duplicate values can be discarded, even though RFC 2426 doesn't explicitly
    say this. I.e., assumes that TYPE=WORK,VOICE,WORK === TYPE=VOICE,WORK.
    """
    values = set(vcard_utils.split_unescaped(values_string, ","))

    # Validate
    for value in values:
        if not re.match(
            f'^[{SAFE_REGEX_CHARACTERS}]+$|^"[{QUOTE_SAFE_REGEX_CHARACTERS}]+"$', value
        ):
            raise VCardValueError(f"{NOTE_INVALID_VALUE}: {value}", {})

    return values
