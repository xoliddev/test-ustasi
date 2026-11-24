"""The refusal error every rule raises (``code`` maps to an ``err.<code>`` text in shared/locales) and the AI error."""

from __future__ import annotations


class Refused(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class AIError(Exception):
    """The model could not draft (network, HTTP status, an answer that is not the agreed JSON). Never shown as is."""
