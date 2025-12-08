# src/lexer.py

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

        # Order matters: longer patterns first where needed
        self.token_specification = [
            ("COMMENT",   r"#.*"),                 # Comment till end of line
            ("WHITESPACE", r"[ \t\r\n]+"),         # Spaces, tabs, newlines
            ("KEYWORD",   r"\b(data|select|filter|sum|max|min|count|between|from|even|odd|print|and)\b"),
            ("NUM",       r"[0-9]+"),
            ("ID",        r"[A-Za-z_][A-Za-z0-9_]*"),
            ("LBRACKET",  r"\["),
            ("RBRACKET",  r"\]"),
            ("COMMA",     r","),
            ("GT",        r">"),
            ("LT",        r"<"),
            ("ASSIGN",    r"="),
            ("MISMATCH",  r"."),                   # Any other single character
        ]

        parts = [f"(?P<{name}>{pattern})" for name, pattern in self.token_specification]
        self.master_pattern = re.compile("|".join(parts))

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        for match in self.master_pattern.finditer(self.source):
            kind = match.lastgroup
            value = match.group()
            start_index = match.start()

            # Compute line and column from the substring
            line, col = self._compute_line_column(start_index)

            if kind == "WHITESPACE":
                continue
            if kind == "COMMENT":
                continue
            if kind == "KEYWORD":
                # Store as uppercase type of the keyword itself for clarity
                token_type = value.upper()
                tokens.append(Token(token_type, value, line, col))
            elif kind in ("ID", "NUM", "LBRACKET", "RBRACKET", "COMMA", "GT", "LT", "ASSIGN"):
                tokens.append(Token(kind, value, line, col))
            elif kind == "MISMATCH":
                raise LexerError(f"Unexpected character {value!r} at line {line}, column {col}")

        return tokens

    def _compute_line_column(self, index: int) -> (int, int):
        """
        Compute line and column for a given absolute index in self.source
        This is simple and fine for our project scale.
        """
        text_up_to_index = self.source[:index]
        line = text_up_to_index.count("\n") + 1
        if "\n" in text_up_to_index:
            last_newline_pos = text_up_to_index.rfind("\n")
            column = index - last_newline_pos
        else:
            column = index + 1
        return line, column
