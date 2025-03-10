#!/usr/bin/env python
import sys
from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Sequence

from .vcard_errors import UsageError
from .vcard_validator import VcardValidator

PATH_ARGUMENT_HELP = "The files to validate. Use '-' for standard input"
VERBOSE_OPTION_HELP = "Enable verbose output"


def main() -> int:
    try:
        arguments = parse_arguments(sys.argv[1:])
    except UsageError as error:
        sys.stderr.write(f"{str(error)}\n")
        return 2

    return_code = 0
    for filename in arguments.paths:
        result = VcardValidator(filename, arguments.verbose).result
        if result != "":
            print(result)
            return_code = 1

    return return_code


def parse_arguments(arguments: Sequence[str]) -> Namespace:
    argument_parser = ArgumentParser()
    argument_parser.add_argument(
        "--verbose", default=False, action="store_true", help=VERBOSE_OPTION_HELP
    )
    argument_parser.add_argument("paths", metavar="path", nargs="+", help=PATH_ARGUMENT_HELP)
    try:
        parsed_arguments = argument_parser.parse_args(args=arguments)
    except ArgumentError as error:
        raise UsageError("Invalid argument") from error
    return parsed_arguments


if __name__ == "__main__":
    sys.exit(main())
