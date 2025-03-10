from typing import List, MutableMapping, Set


class VcardProperty:  # pylint: disable=too-few-public-methods
    parameters: MutableMapping[str, Set[str]]

    def __init__(self, name: str, values: List[List[str]]):
        self.name = name
        self.values = values
        self.parameters = {}
