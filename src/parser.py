# src/parser.py

from dataclasses import dataclass
from typing import List, Optional
from lexer import Token


# ============================
# AST NODE DEFINITIONS
# ============================

@dataclass
class ProgramNode:
    statements: list


@dataclass
class DataDeclarationNode:
    name: str
    values: list  # list of integers


@dataclass
class SelectQueryNode:
    condition: tuple   # (">", 5)  OR ("between", 2, 8)
    source: str


@dataclass
class FilterQueryNode:
    mode: str          # "even" or "odd"
    source: str


@dataclass
class AssignmentNode:
    target: str
    expr: object       # SelectQueryNode or FilterQueryNode or AggregationNode


@dataclass
class AggregationNode:
    func: str          # sum / max / min / count
    source: str


@dataclass
class PrintNode:
    target: str


# ============================
# PARSER LOGIC
# ============================

class ParserError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # -------------------------
    # Utility functions
    # -------------------------

    def current(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def eat(self, token_type: str) -> Token:
        tok = self.current()

        if tok is None:
            raise ParserError(f"Unexpected end of input. Expected {token_type}")

        if tok.type != token_type:
            raise ParserError(
                f"Expected {token_type}, got {tok.type} ({tok.value}) "
                f"at line {tok.line}"
            )

        self.pos += 1
        return tok

    # -------------------------
    # Grammar starting point
    # program → statements
    # -------------------------

    def parse(self):
        statements = []
        while self.current() is not None:
            stmt = self.statement()
            statements.append(stmt)
        return ProgramNode(statements)

    # -------------------------
    # statement → data_decl | query | assignment | aggregation | print
    # -------------------------

    def statement(self):
        tok = self.current()

        if tok.type == "DATA":
            return self.data_decl()

        if tok.type in ("SELECT", "FILTER"):
            return self.query()

        if tok.type == "ID":
            return self.assignment()

        if tok.type in ("SUM", "MAX", "MIN", "COUNT"):
            return self.aggregation()

        if tok.type == "PRINT":
            return self.print_stmt()

        raise ParserError(f"Unexpected token {tok.type} at line {tok.line}")

    # -------------------------
    # data_decl → data ID = [ numlist ]
    # -------------------------

    def data_decl(self):
        self.eat("DATA")
        name = self.eat("ID").value
        self.eat("ASSIGN")
        self.eat("LBRACKET")

        # NUM ( , NUM )*
        numbers = [int(self.eat("NUM").value)]

        while self.current() and self.current().type == "COMMA":
            self.eat("COMMA")
            numbers.append(int(self.eat("NUM").value))

        self.eat("RBRACKET")
        return DataDeclarationNode(name, numbers)

    # -------------------------
    # query → SELECT condition FROM ID
    #        | FILTER (even|odd) FROM ID
    # -------------------------

    def query(self):
        tok = self.current()

        # FILTER QUERY
        if tok.type == "FILTER":
            self.eat("FILTER")

            mode_token = self.current()

            if mode_token.type == "EVEN":
                mode = self.eat("EVEN").value
            elif mode_token.type == "ODD":
                mode = self.eat("ODD").value
            else:
                raise ParserError(f"Expected even/odd at line {tok.line}")

            self.eat("FROM")
            source = self.eat("ID").value
            return FilterQueryNode(mode, source)

        # SELECT QUERY
        if tok.type == "SELECT":
            self.eat("SELECT")
            cond = self.parse_condition()
            self.eat("FROM")
            source = self.eat("ID").value
            return SelectQueryNode(cond, source)

        raise ParserError(f"Invalid query at line {tok.line}")

    # -------------------------
    # condition → > NUM | < NUM | = NUM | between NUM and NUM
    # -------------------------

    def parse_condition(self):
        tok = self.current()

        # >
        if tok.type == "GT":
            self.eat("GT")
            num = int(self.eat("NUM").value)
            return (">", num)

        # <
        if tok.type == "LT":
            self.eat("LT")
            num = int(self.eat("NUM").value)
            return ("<", num)

        # =
        if tok.type == "ASSIGN":   # This is '='
            self.eat("ASSIGN")
            num = int(self.eat("NUM").value)
            return ("=", num)

        # BETWEEN
        if tok.type == "BETWEEN":
            self.eat("BETWEEN")
            a = int(self.eat("NUM").value)
            self.eat("AND")   # MUST be in keyword list
            b = int(self.eat("NUM").value)
            return ("between", a, b)

        raise ParserError(f"Invalid condition near line {tok.line}")

    # -------------------------
    # assignment → ID = (query | aggregation)
    # -------------------------

    def assignment(self):
        target = self.eat("ID").value
        self.eat("ASSIGN")

        next_token = self.current().type

        if next_token in ("SELECT", "FILTER"):
            expr = self.query()

        elif next_token in ("SUM", "MAX", "MIN", "COUNT"):
            expr = self.aggregation()

        else:
            raise ParserError(f"Invalid RHS in assignment at line {self.current().line}")

        return AssignmentNode(target, expr)

    # -------------------------
    # aggregation → (SUM|MAX|MIN|COUNT) FROM ID
    # -------------------------

    def aggregation(self):
        func = self.current().type.lower()
        self.eat(self.current().type)
        self.eat("FROM")
        src = self.eat("ID").value
        return AggregationNode(func, src)

    # -------------------------
    # print → PRINT ID
    # -------------------------

    def print_stmt(self):
        self.eat("PRINT")
        target = self.eat("ID").value
        return PrintNode(target)
