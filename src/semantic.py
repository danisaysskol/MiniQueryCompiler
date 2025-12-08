# src/semantic.py

from dataclasses import dataclass
from typing import Dict, Optional

from parser import (
    ProgramNode,
    DataDeclarationNode,
    SelectQueryNode,
    FilterQueryNode,
    AssignmentNode,
    AggregationNode,
    PrintNode,
)


class SemanticError(Exception):
    """Raised when a semantic rule is violated."""
    pass


@dataclass
class Symbol:
    name: str
    type: str              # "list<int>" or "int"
    element_type: Optional[str] = None  # e.g. "int" for list<int>
    size: Optional[int] = None          # for lists


class SemanticAnalyzer:
    def __init__(self):
        # Simple global symbol table (no nested scopes needed for MiniQuery)
        self.symbols: Dict[str, Symbol] = {}

    # -------------------------
    # Public entry point
    # -------------------------
    def analyze(self, program: ProgramNode) -> Dict[str, Symbol]:
        """
        Walk the AST, build symbol table, and enforce semantic rules.
        """
        for stmt in program.statements:
            self._check_statement(stmt)
        return self.symbols

    # -------------------------
    # Statement dispatcher
    # -------------------------
    def _check_statement(self, node):
        if isinstance(node, DataDeclarationNode):
            self._check_data_decl(node)
        elif isinstance(node, AssignmentNode):
            self._check_assignment(node)
        elif isinstance(node, SelectQueryNode):
            self._infer_select(node)  # allowed as top-level (ignored result)
        elif isinstance(node, FilterQueryNode):
            self._infer_filter(node)  # allowed as top-level
        elif isinstance(node, AggregationNode):
            self._infer_aggregation(node)  # allowed as top-level
        elif isinstance(node, PrintNode):
            self._check_print(node)
        else:
            raise SemanticError(f"Unknown AST node: {node}")

    # -------------------------
    # Data declarations
    # data nums = [1,2,3]
    # -------------------------
    def _check_data_decl(self, node: DataDeclarationNode):
        # All values must be integers (parser already ensures, but we re-assert)
        for v in node.values:
            if not isinstance(v, int):
                raise SemanticError(f"Non-integer value in list for {node.name}")

        if node.name in self.symbols:
            # You can choose: either allow overwrite or make it error.
            # Here we make it error to keep things clean.
            raise SemanticError(f"Redeclaration of variable '{node.name}'")

        sym = Symbol(
            name=node.name,
            type="list<int>",
            element_type="int",
            size=len(node.values),
        )
        self.symbols[node.name] = sym
        # Optional: annotate node with type
        setattr(node, "inferred_type", "list<int>")

    # -------------------------
    # Assignment
    # big = select >5 from nums
    # total = sum from nums
    # -------------------------
    def _check_assignment(self, node: AssignmentNode):
        expr_type = self._infer_expr(node.expr)

        # If variable already exists with different type, that's an error
        if node.target in self.symbols:
            existing = self.symbols[node.target]
            if existing.type != expr_type:
                raise SemanticError(
                    f"Type mismatch assigning to '{node.target}': "
                    f"{existing.type} vs {expr_type}"
                )
            # Same type, allowed – treat as re-assignment
        else:
            # New symbol
            if expr_type == "list<int>":
                sym = Symbol(
                    name=node.target,
                    type="list<int>",
                    element_type="int",
                )
            elif expr_type == "int":
                sym = Symbol(
                    name=node.target,
                    type="int",
                )
            else:
                raise SemanticError(
                    f"Unsupported expression type '{expr_type}' for '{node.target}'"
                )

            self.symbols[node.target] = sym

        setattr(node, "inferred_type", expr_type)

    # -------------------------
    # Expression type inference dispatcher
    # -------------------------
    def _infer_expr(self, node) -> str:
        if isinstance(node, SelectQueryNode):
            return self._infer_select(node)
        if isinstance(node, FilterQueryNode):
            return self._infer_filter(node)
        if isinstance(node, AggregationNode):
            return self._infer_aggregation(node)
        raise SemanticError(f"Invalid expression node: {node}")

    # -------------------------
    # SELECT queries
    # select >5 from nums
    # select between 2 and 8 from nums
    # -------------------------
    def _infer_select(self, node: SelectQueryNode) -> str:
        # Check source list variable
        src_name = node.source
        src_sym = self._require_list_symbol(src_name)

        # Check condition tuple
        cond = node.condition
        op = cond[0]

        if op in (">", "<", "="):
            if not isinstance(cond[1], int):
                raise SemanticError("Condition value must be an integer")
        elif op == "between":
            if not (isinstance(cond[1], int) and isinstance(cond[2], int)):
                raise SemanticError("Both bounds in 'between' must be integers")
        else:
            raise SemanticError(f"Unknown condition operator '{op}'")

        # Result of SELECT is a list of same element type
        result_type = "list<int>"  # since we only have int lists
        setattr(node, "inferred_type", result_type)
        return result_type

    # -------------------------
    # FILTER queries
    # filter even from nums
    # filter odd from nums
    # -------------------------
    def _infer_filter(self, node: FilterQueryNode) -> str:
        # Source must be a list<int>
        src_sym = self._require_list_symbol(node.source)

        if node.mode not in ("even", "odd"):
            raise SemanticError(f"Invalid filter mode '{node.mode}'")

        result_type = "list<int>"
        setattr(node, "inferred_type", result_type)
        return result_type

    # -------------------------
    # Aggregations
    # sum from nums
    # max from nums
    # -------------------------
    def _infer_aggregation(self, node: AggregationNode) -> str:
        # Input must be list<int>
        src_sym = self._require_list_symbol(node.source)

        if node.func not in ("sum", "max", "min", "count"):
            raise SemanticError(f"Unknown aggregation '{node.func}'")

        # Aggregation returns a single integer
        result_type = "int"
        setattr(node, "inferred_type", result_type)
        return result_type

    # -------------------------
    # Print
    # print big
    # -------------------------
    def _check_print(self, node: PrintNode):
        if node.target not in self.symbols:
            raise SemanticError(f"Use of undeclared variable '{node.target}' in print")
        # No type restriction: we allow printing any declared type

    # -------------------------
    # Helpers
    # -------------------------
    def _require_symbol(self, name: str) -> Symbol:
        if name not in self.symbols:
            raise SemanticError(f"Use of undeclared variable '{name}'")
        return self.symbols[name]

    def _require_list_symbol(self, name: str) -> Symbol:
        sym = self._require_symbol(name)
        if sym.type != "list<int>":
            raise SemanticError(
                f"Variable '{name}' must be a list<int>, found {sym.type}"
            )
        return sym
