"""
vCard v3.0 (RFC 2426) validating functions

Should contain all the general purpose validation code extracted from
standards.
"""

import re
from typing import Any, List, MutableMapping, Set, Tuple
from urllib.parse import urlparse
from warnings import warn

from dateutil.parser import isoparse

from .vcard_definitions import (
    DOUBLE_QUOTE_CHARACTER,
    ID_REGEX_CHARACTERS,
    QUOTE_SAFE_REGEX_CHARACTERS,
    REGEX_ESCAPED_CHARACTERS,
    SAFE_REGEX_CHARACTERS,
    SPACE_CHARACTER,
)
from .vcard_errors import (  # Error literals; Functions; Classes
    NOTE_INVALID_DATE,
    NOTE_INVALID_LANGUAGE_VALUE,
    NOTE_INVALID_PARAMETER_NAME,
    NOTE_INVALID_PARAMETER_VALUE,
    NOTE_INVALID_SUB_VALUE,
    NOTE_INVALID_SUB_VALUE_COUNT,
    NOTE_INVALID_TEXT_VALUE,
    NOTE_INVALID_TIME_ZONE,
    NOTE_INVALID_URI,
    NOTE_INVALID_VALUE,
    NOTE_INVALID_VALUE_COUNT,
    NOTE_INVALID_X_NAME,
    NOTE_MISMATCH_PARAMETER,
    NOTE_MISSING_PARAMETER,
    NOTE_NON_EMPTY_PARAMETER,
    WARN_DEFAULT_TYPE_VALUE,
    WARN_INVALID_EMAIL_TYPE,
    WARN_MULTIPLE_NAMES,
    VCardError,
    VCardItemCountError,
    VCardNameError,
    VCardValueError,
)
from .vcard_property import VcardProperty

VALID_DATE = re.compile(r"^\d{4}-?\d{2}-?\d{2}$")
VALID_TIMEZONE = re.compile(r"^(Z|[+-]\d{2}:?\d{2})$")
VALID_TIME_WITH_TIMEZONE = re.compile(r"^(\d{2}:?\d{2}:?\d{2}(?:,\d+)?)(.*)$")
VALID_LANGUAGE_TAG = re.compile(r"^([a-z]{1,8})(-[a-z]{1,8})*$")
VALID_X_NAME = re.compile(rf"^X-[{ID_REGEX_CHARACTERS}]+$")
VALID_PRESENTATION_TEXT = re.compile(f"^[{SAFE_REGEX_CHARACTERS}]*$")
VALID_TEXT = re.compile(
    f"^([{SAFE_REGEX_CHARACTERS}:{DOUBLE_QUOTE_CHARACTER}]|(\\\\[{REGEX_ESCAPED_CHARACTERS}]))*$"
)
VALID_QUOTED_STRING = re.compile(
    f"^{DOUBLE_QUOTE_CHARACTER}[{QUOTE_SAFE_REGEX_CHARACTERS}]{DOUBLE_QUOTE_CHARACTER}$"
)
VALID_FLOAT = re.compile(r"^[+-]?\d+(\.\d+)?$")

LABEL_TYPE_VALUES = ("dom", "intl", "postal", "parcel", "home", "work", "pref")
TELEPHONE_TYPE_VALUES = (
    "home",
    "msg",
    "work",
    "pref",
    "voice",
    "fax",
    "cell",
    "video",
    "pager",
    "bbs",
    "modem",
    "car",
    "isdn",
    "pcs",
)
EMAIL_TYPE_VALUES = ("internet", "x400", "pref", "dom", "intl", "postal", "parcel", "home", "work")


def _expect_no_parameters(property_: VcardProperty) -> None:
    parameters = __get_parameters(property_)
    if parameters:
        raise VCardItemCountError(f"{NOTE_NON_EMPTY_PARAMETER}: {parameters}", {})


def _expect_parameters(property_: VcardProperty) -> None:
    if not __get_parameters(property_):
        raise VCardItemCountError(NOTE_MISSING_PARAMETER, {})


def _expect_value_count(values: List[Any], count: int) -> None:
    if len(values) != count:
        raise VCardItemCountError(
            f"{NOTE_INVALID_VALUE_COUNT}: {len(values)} (expected {count})", {}
        )


def _expect_sub_value_count(sub_values: List[str], count: int) -> None:
    if len(sub_values) != count:
        raise VCardItemCountError(
            f"{NOTE_INVALID_SUB_VALUE_COUNT}: {len(sub_values)} (expected {count})", {}
        )


def _expect_parameter_values(param_values: Set[str], expected_param_values: Set[str]) -> None:
    if param_values != expected_param_values:
        raise VCardValueError(f"{NOTE_INVALID_PARAMETER_VALUE}: {param_values}", {})


def _expect_no_parameter(
    parameters: MutableMapping[str, Set[str]], parameter_name: str, conflicting_parameter_name: str
) -> None:
    if conflicting_parameter_name in parameters:
        raise VCardValueError(
            f"{NOTE_MISMATCH_PARAMETER}: {parameter_name} and {conflicting_parameter_name}", {}
        )


def validate_date(text: str) -> None:
    """
    Based on https://datatracker.ietf.org/doc/html/rfc2425#section-5.8.4 and the fact
    that it specifies a subset of ISO 8601.

    @param text: String
    """
    if VALID_DATE.match(text) is None:
        raise VCardValueError(NOTE_INVALID_DATE, {"String": text})

    try:
        isoparse(text)
    except ValueError as error:
        raise VCardValueError(NOTE_INVALID_DATE, {"String": text}) from error


def validate_time_zone(text: str) -> None:
    """
    Based on https://datatracker.ietf.org/doc/html/rfc2425#section-5.8.4 and the fact
    that it specifies a subset of ISO 8601.

    @param text: String

    Examples:
    >>> validate_time_zone('Z')
    >>> validate_time_zone('+01:00')
    >>> validate_time_zone('-12:30')
    >>> validate_time_zone('+23:59')
    >>> validate_time_zone('-0001')
    >>> validate_time_zone('-00:30')
    >>> validate_time_zone('+00:30')
    >>> validate_time_zone('Z+01:00') # Can't combine Z and offset
    ... # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid time zone ...
    String: Z+01:00
    >>> validate_time_zone('+1:00') # Need preceding zero
    ... # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid time zone ...
    String: +1:00
    >>> validate_time_zone('0100') # Need + or -
    ... # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid time zone ...
    String: 0100
    >>> validate_time_zone('01') # Need colon and minutes
    ... # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid time zone ...
    String: 01
    >>> validate_time_zone('01:') # Need minutes
    ... # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid time zone ...
    String: 01:
    >>> validate_time_zone('01:1') # Need preceding zero
    ... # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid time zone ...
    """
    if not VALID_TIMEZONE.match(text):
        raise VCardValueError(NOTE_INVALID_TIME_ZONE, {"String": text})

    try:
        isoparse(f"2000-01-01 00:00:00.0{text}")
    except ValueError as error:
        raise VCardValueError(NOTE_INVALID_TIME_ZONE, {"String": text}) from error


def validate_language_tag(text: str) -> None:
    """
    langval, as defined by RFC 1766 <https://datatracker.ietf.org/doc/html/rfc1766>

    @param text: String

    Examples:
    >>> validate_language_tag('en')
    >>> validate_language_tag('-US') # Need primary tag # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid language (See RFC 1766 section 2 for details)
    String: -us
    >>> validate_language_tag('en-') # Can't end with dash # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid language (See RFC 1766 section 2 for details)
    String: en-
    >>> validate_language_tag('en-US')

    """
    text = text.lower()  # Case insensitive

    if VALID_LANGUAGE_TAG.match(text) is None:
        raise VCardValueError(NOTE_INVALID_LANGUAGE_VALUE, {"String": text})

    # Extend to validate according to referenced ISO/RFC standards


def validate_x_name(text: str) -> None:
    """
    @param text: Single parameter name

    Examples:
    >>> validate_x_name('X-abc')
    >>> from vcard.vcard_definitions import ID_CHARACTERS
    >>> validate_x_name(f'X-{ID_CHARACTERS}')
    >>> validate_x_name('X-') # Have to have more characters # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardNameError: Invalid X-name (See RFC 2426 section 4 for x-name syntax)
    String: X-
    >>> validate_x_name('') # Have to start with X- #doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    VCardNameError: Invalid X-name (See RFC 2426 section 4 for x-name syntax)
    ...
    >>> validate_x_name('x-abc') # X must be upper case # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardNameError: Invalid X-name (See RFC 2426 section 4 for x-name syntax)
    String: x-abc
    >>> validate_x_name('foo') # Have to start with X- # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardNameError: Invalid X-name (See RFC 2426 section 4 for x-name syntax)
    String: foo
    """
    if VALID_X_NAME.match(text) is None:
        raise VCardNameError(NOTE_INVALID_X_NAME, {"String": text})


def validate_presentation_text(text: str) -> None:
    """
    ptext, as described on page 28
    <https://datatracker.ietf.org/doc/html/rfc2426#section-4>

    @param text: String

    Examples:
    >>> from vcard.vcard_definitions import SAFE_CHARACTERS
    >>> validate_presentation_text('')
    >>> validate_presentation_text(SAFE_CHARACTERS)
    >>> validate_presentation_text(u'\u000B') #doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid parameter value ...
    String: ...
    """
    if VALID_PRESENTATION_TEXT.match(text) is None:
        raise VCardValueError(NOTE_INVALID_PARAMETER_VALUE, {"String": text})


def validate_text_value(text: str) -> None:
    """
    text-value, as described on page 37
    <https://datatracker.ietf.org/doc/html/rfc2426#section-4>

    @param text: String

    Examples:
    >>> from vcard.vcard_definitions import SAFE_CHARACTERS
    >>> validate_text_value('')
    >>> validate_text_value('\\\\,')
    >>> validate_text_value(SAFE_CHARACTERS)
    >>> validate_text_value('\\\\n')
    >>> validate_text_value(';') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid text value (See RFC 2426 section 4 for details)
    String: ...
    >>> validate_text_value('\\\\\\\\;') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid text value (See RFC 2426 section 4 for details)
    String: ...
    """
    if VALID_TEXT.match(text) is None:
        raise VCardValueError(NOTE_INVALID_TEXT_VALUE, {"String": text})


def validate_quoted_string(text: str) -> None:
    """
    quoted-string, as described on page 28
    <https://datatracker.ietf.org/doc/html/rfc2426#section-4>

    @param text: String

    Examples:
    >>> from vcard.vcard_definitions import QUOTE_SAFE_CHARACTERS
    >>> validate_quoted_string(
    ...     f"{DOUBLE_QUOTE_CHARACTER}{QUOTE_SAFE_CHARACTERS[0]}{DOUBLE_QUOTE_CHARACTER}"
    ... ) # doctest: +ELLIPSIS
    >>> validate_quoted_string(
    ...     f"{DOUBLE_QUOTE_CHARACTER}{DOUBLE_QUOTE_CHARACTER}"
    ... ) # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid parameter value ...
    >>> validate_quoted_string(
    ...     f"{DOUBLE_QUOTE_CHARACTER}{QUOTE_SAFE_CHARACTERS[-1]*2}{DOUBLE_QUOTE_CHARACTER}"
    ... ) # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid parameter value ...
    String: "ÿÿ"
    """
    if VALID_QUOTED_STRING.match(text) is None:
        raise VCardValueError(NOTE_INVALID_PARAMETER_VALUE, {"String": text})


def validate_param_value(text: str) -> None:
    """
    param-value, as described on page 28
    <https://datatracker.ietf.org/doc/html/rfc2426#section-4>

    @param text: Single parameter value

    Examples:
    >>> from vcard.vcard_definitions import QUOTE_SAFE_CHARACTERS, SAFE_CHARACTERS
    >>> validate_param_value('')
    >>> validate_param_value(SAFE_CHARACTERS)
    >>> validate_param_value(
    ...     f"{DOUBLE_QUOTE_CHARACTER}{QUOTE_SAFE_CHARACTERS[0]}{DOUBLE_QUOTE_CHARACTER}"
    ... ) # doctest: +ELLIPSIS
    >>> validate_param_value(
    ...     f"{DOUBLE_QUOTE_CHARACTER}{DOUBLE_QUOTE_CHARACTER}"
    ... ) # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid parameter value ...
    String: ""
    """
    try:
        validate_presentation_text(text)
    except VCardValueError:
        try:
            validate_quoted_string(text)
        except VCardValueError as error:
            raise VCardValueError(NOTE_INVALID_PARAMETER_VALUE, {"String": text}) from error


def validate_text_parameter(parameter: Tuple[str, Set[str]]) -> None:
    """
    text-param, as described on page 35
    <https://datatracker.ietf.org/doc/html/rfc2426#section-4>

    @param parameter: Single parameter, as returned by get_vcard_property_param

    Examples:
    >>> validate_text_parameter(('VALUE', {'ptext'}))
    """
    param_name = parameter[0].upper()
    param_values = parameter[1]

    if param_name == "VALUE":
        if param_values != {"ptext"}:
            raise VCardValueError(f"{NOTE_INVALID_PARAMETER_VALUE}: {param_values}", {})
        return
    if param_name == "LANGUAGE":
        if len(param_values) != 1:
            raise VCardValueError(f"{NOTE_INVALID_PARAMETER_VALUE}: {param_values}", {})
        for param_value in param_values:
            validate_language_tag(param_value)
    else:
        validate_x_name(param_name)
        if len(param_values) != 1:
            raise VCardValueError(f"{NOTE_INVALID_PARAMETER_VALUE}: {param_values}", {})
        validate_param_value(param_values.pop())


def validate_float(text: str) -> None:
    """
    float value, as described on page 10 of RFC 2425
    <https://datatracker.ietf.org/doc/html/rfc2425#section-5.8.4>

    Examples:
    >>> validate_float('12')
    >>> validate_float('12.345')
    >>> validate_float('+12.345')
    >>> validate_float('-12.345')
    >>> validate_float('12.') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    VCardValueError: Invalid sub-value ...
    >>> validate_float('.12') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    VCardValueError: Invalid sub-value ...
    >>> validate_float('foo') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    VCardValueError: Invalid sub-value ...
    >>> validate_float('++12.345') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    VCardValueError: Invalid sub-value ...
    >>> validate_float('--12.345') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    VCardValueError: Invalid sub-value ...
    >>> validate_float('12.34.5') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    VCardValueError: Invalid sub-value ...
    """
    if VALID_FLOAT.match(text) is None:
        raise VCardValueError(f"{NOTE_INVALID_SUB_VALUE}, expected float value: {text}", {})


def validate_uri(text: str) -> None:
    """
    genericurl, as described in RFC 1738
    <https://datatracker.ietf.org/doc/html/rfc1738#section-5>.
    @param text: Single parameter value

    Examples:
    >>> validate_uri('https://example.org/')
    >>> validate_uri('https\\\\://example.org/') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid URI ...
    String: https\\://example.org/
    >>> validate_uri('https:') # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    VCardValueError: Invalid URI ...
    String: https:
    """
    parts = urlparse(text)
    if parts[0] == "" or (parts[1] == "" and parts[2] == ""):
        raise VCardValueError(NOTE_INVALID_URI, {"String": text})


def validate_vcard_property(property_: VcardProperty) -> None:
    """
    Checks any property according to
    <https://datatracker.ietf.org/doc/html/rfc2426#section-3> and
    <https://datatracker.ietf.org/doc/html/rfc2426#section-4>. Checks are grouped by
    property to allow easy overview rather than a short function.

    @param property_: Formatted property
    """
    property_name = property_.name.upper()

    try:
        {
            "ADR": handle_adr,
            "AGENT": handle_agent,
            "BDAY": handle_bday,
            "BEGIN": handle_begin_end,
            "EMAIL": handle_email,
            "END": handle_begin_end,
            "FN": handle_fn,
            "GEO": handle_geo,
            "LABEL": handle_label,
            "LOGO": handle_photo_logo,
            "MAILER": handle_mailer,
            "N": handle_n,
            "NAME": handle_name,
            "NICKNAME": handle_nickname,
            "PHOTO": handle_photo_logo,
            "PROFILE": handle_profile,
            "ROLE": handle_role,
            "SOURCE": handle_source,
            "TEL": handle_tel,
            "TITLE": handle_title,
            "TZ": handle_tz,
            "URL": handle_url,
            "VERSION": handle_version,
        }[property_name](property_)
    except KeyError:
        pass  # No validation implemented
    except VCardError as error:
        error.context["Property"] = property_name
        raise


def handle_url(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.6.8>
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 1)
    validate_uri(property_.values[0][0])


def handle_agent(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.5.4>
    if property_.parameters is not None:
        for parameter_name, param_values in property_.parameters.items():
            if parameter_name.upper() != "VALUE":
                raise VCardNameError(f"{NOTE_INVALID_PARAMETER_NAME}: {param_values}", {})
            if param_values != {"uri"}:
                raise VCardValueError(f"{NOTE_INVALID_PARAMETER_VALUE}: {param_values}", {})
        _expect_value_count(property_.values, 1)
        # can this be...
        #   _expect_sub_value_count(property_.values[0], 1)
        # ...?
        for value in property_.values:
            if len(value) != 1:
                raise VCardItemCountError(
                    f"{NOTE_INVALID_SUB_VALUE_COUNT}: {len(property_.values[0])} (expected 1)", {}
                )
            validate_uri(value[0])
    else:
        # Inline vCard object
        # Un-escape and validate value
        raise NotImplementedError


def handle_role(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.5.2>
    if property_.parameters is not None:
        for parameter in property_.parameters.items():
            validate_text_parameter(parameter)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    validate_text_value(property_.values[0][0])


def handle_title(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.5.1>
    if property_.parameters is not None:
        for parameter in property_.parameters.items():
            validate_text_parameter(parameter)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    validate_text_value(property_.values[0][0])


def handle_geo(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.4.2>
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 2)
    # can the following be...
    #   _expect_sub_value_count(property_.values[0], 2)
    # ...?
    for value in property_.values:
        if len(value) != 1:
            raise VCardItemCountError(
                f"{NOTE_INVALID_SUB_VALUE_COUNT}: {len(property_.values[0])} (expected 1)", {}
            )
        validate_float(value[0])


def handle_tz(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.4.1>
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    sub_value = property_.values[0][0]
    validate_time_zone(sub_value)


def handle_mailer(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.3.3>
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 1)
    _expect_value_count(property_.values[0], 1)
    validate_text_value(property_.values[0][0])


def handle_email(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.3.2>
    if property_.parameters is not None:
        for parameter_name, param_values in property_.parameters.items():
            if parameter_name.upper() == "TYPE":
                for param_sub_value in param_values:
                    if param_sub_value.lower() not in EMAIL_TYPE_VALUES:
                        warn(f"{WARN_INVALID_EMAIL_TYPE}: {param_sub_value}")
                if ["internet"] == [value.lower() for value in param_values]:
                    warn(f"{WARN_DEFAULT_TYPE_VALUE}: {property_.values}")
            else:
                raise VCardNameError(f"{NOTE_INVALID_PARAMETER_NAME}: {parameter_name}", {})
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    validate_text_value(property_.values[0][0])


def handle_tel(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.3.1>
    if property_.parameters is not None:
        for parameter_name, param_values in property_.parameters.items():
            if parameter_name.upper() == "TYPE":
                for param_sub_value in param_values:
                    if param_sub_value.lower() not in TELEPHONE_TYPE_VALUES:
                        raise VCardValueError(
                            f"{NOTE_INVALID_PARAMETER_VALUE}: {param_sub_value}", {}
                        )
                if ["voice"] == [value.lower() for value in param_values]:
                    warn(f"{WARN_DEFAULT_TYPE_VALUE}: {property_.values}")
            else:
                raise VCardNameError(f"{NOTE_INVALID_PARAMETER_NAME}: {parameter_name}", {})
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)


def handle_label(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.2.2>
    if property_.parameters is not None:
        for parameter_name, param_values in property_.parameters.items():
            if parameter_name.upper() == "TYPE":
                for param_sub_value in param_values:
                    if param_sub_value not in LABEL_TYPE_VALUES:
                        raise VCardValueError(
                            f"{NOTE_INVALID_PARAMETER_VALUE}: {param_sub_value}", {}
                        )
                if param_values == {"intl", "postal", "parcel", "work"}:
                    warn(f"{WARN_DEFAULT_TYPE_VALUE}: {property_.values}")
            else:
                for parameter in property_.parameters.items():
                    validate_text_parameter(parameter)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    validate_text_value(property_.values[0][0])


def handle_adr(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.2.1>
    _expect_value_count(property_.values, 7)
    if property_.parameters is not None:
        for parameter_name, param_values in property_.parameters.items():
            if parameter_name.upper() == "TYPE":
                for param_sub_value in param_values:
                    if param_sub_value not in LABEL_TYPE_VALUES:
                        raise VCardValueError(
                            f"{NOTE_INVALID_PARAMETER_VALUE}: {param_sub_value}", {}
                        )
                if param_values == {"intl", "postal", "parcel", "work"}:
                    warn(f"{WARN_DEFAULT_TYPE_VALUE}: {property_.values}")
            else:
                for parameter in property_.parameters.items():
                    validate_text_parameter(parameter)


def handle_bday(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.1.5>
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    validate_date(property_.values[0][0])


def handle_photo_logo(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.1.4>
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.5.4>
    _expect_parameters(property_)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    for parameter_name, param_values in property_.parameters.items():
        upper_parameter_name = parameter_name.upper()
        if upper_parameter_name == "ENCODING":
            _expect_parameter_values(param_values, {"b"})
            _expect_no_parameter(property_.parameters, upper_parameter_name, "VALUE")
        elif upper_parameter_name == "TYPE" and "ENCODING" not in property_.parameters:
            raise VCardItemCountError(f"{NOTE_MISSING_PARAMETER}: {'ENCODING'}", {})
        elif upper_parameter_name == "VALUE":
            _expect_parameter_values(param_values, {"uri"})
            validate_uri(property_.values[0][0])
        elif upper_parameter_name not in ["ENCODING", "TYPE", "VALUE"]:
            raise VCardNameError(f"{NOTE_INVALID_PARAMETER_NAME}: {parameter_name}", {})


def handle_nickname(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.1.3>
    if property_.parameters is not None:
        for parameter in property_.parameters.items():
            validate_text_parameter(parameter)
    _expect_value_count(property_.values, 1)


def handle_n(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.1.2>
    if property_.parameters is not None:
        for parameter in property_.parameters.items():
            validate_text_parameter(parameter)
    _expect_value_count(property_.values, 5)
    # Should names be split?
    for names in property_.values:
        for name in names:
            validate_text_value(name)
            if (
                name.find(SPACE_CHARACTER) != -1
                and "".join(["".join(names) for names in property_.values]) != name
            ):
                # Space in name
                # Not just a single name
                warn(f"{WARN_MULTIPLE_NAMES}: {name}")


def handle_version(property_: VcardProperty) -> None:
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 1)
    if property_.values[0][0] != "3.0":
        raise VCardValueError(
            f'{NOTE_INVALID_VALUE}: {property_.values[0][0]} (expected "3.0")', {}
        )


def handle_fn(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-3.1.1>
    if property_.parameters is not None:
        for parameter in property_.parameters.items():
            validate_text_parameter(parameter)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    validate_text_value(property_.values[0][0])


def handle_source(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-2.1.4>
    _expect_parameters(property_)
    for parameter_name, param_values in property_.parameters.items():
        if parameter_name.upper() == "VALUE":
            if param_values != {"uri"}:
                raise VCardValueError(f"{NOTE_INVALID_PARAMETER_VALUE}: {param_values}", {})
            if "CONTEXT" in property_.parameters:
                raise VCardValueError(f"{NOTE_MISMATCH_PARAMETER}: {'VALUE'} and {'CONTEXT'}", {})
        elif parameter_name.upper() == "CONTEXT":
            if param_values != {"word"}:
                raise VCardValueError(f"{NOTE_INVALID_PARAMETER_VALUE}: {param_values}", {})
            if "VALUE" in property_.parameters:
                raise VCardValueError(f"{NOTE_MISMATCH_PARAMETER}: {'VALUE'} and {'CONTEXT'}", {})
        else:
            raise VCardNameError(f"{NOTE_INVALID_PARAMETER_NAME}: {parameter_name}", {})


def handle_profile(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-2.1.3>
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    if property_.values[0][0].lower() != "vcard":
        raise VCardValueError(
            f'{NOTE_INVALID_VALUE}: {property_.values[0][0]} (expected "VCARD")', {}
        )
    validate_text_value(property_.values[0][0])


def handle_name(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-2.1.2>
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    validate_text_value(property_.values[0][0])


def handle_begin_end(property_: VcardProperty) -> None:
    # <https://datatracker.ietf.org/doc/html/rfc2426#section-2.1.1>
    _expect_no_parameters(property_)
    _expect_value_count(property_.values, 1)
    _expect_sub_value_count(property_.values[0], 1)
    if property_.values[0][0].lower() != "vcard":
        raise VCardValueError(
            f'{NOTE_INVALID_VALUE}: {property_.values[0][0]} (expected "VCARD")', {}
        )


def __get_parameters(property_: VcardProperty) -> MutableMapping[str, Set[str]]:
    return property_.parameters
