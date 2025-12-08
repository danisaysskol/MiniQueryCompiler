# src/ir_generator.py

from dataclasses import dataclass
from typing import List, Any

from parser import (
    ProgramNode,
    DataDeclarationNode,
    SelectQueryNode,
    FilterQueryNode,
    AssignmentNode,
    AggregationNode,
    PrintNode,
)


@dataclass
class IRInstruction:
    """
    Simple 3-address style instruction.

    op     : operation name (e.g., 'LIST', 'FILTER_GT', 'AGG_SUM', 'ASSIGN', 'PRINT')
    arg1   : first operand (can be variable name, temp name, or literal)
    arg2   : second operand (optional, can be None)
    result : result variable / temp name (optional, can be None)
    """
    op: str
    arg1: Any = None
    arg2: Any = None
    result: Any = None


class IRGenerator:
    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self.temp_counter = 0

    def new_temp(self) -> str:
        """Generate a new temporary variable name."""
        self.temp_counter += 1
        return f"_t{self.temp_counter}"

    # -------------------------
    # Public entry point
    # -------------------------
    def generate(self, program: ProgramNode) -> List[IRInstruction]:
        """
        Generate IR for the whole program.
        """
        self.instructions.clear()
        self.temp_counter = 0

        for stmt in program.statements:
            self._gen_statement(stmt)

        return self.instructions

    # -------------------------
    # Statement dispatcher
    # -------------------------
    def _gen_statement(self, node):
        if isinstance(node, DataDeclarationNode):
            self._gen_data_decl(node)

        elif isinstance(node, AssignmentNode):
            self._gen_assignment(node)

        elif isinstance(node, SelectQueryNode):
            # Standalone query: generate result but ignore it
            temp = self._gen_select(node)
            # No ASSIGN, since not bound to any variable

        elif isinstance(node, FilterQueryNode):
            temp = self._gen_filter(node)

        elif isinstance(node, AggregationNode):
            temp = self._gen_aggregation(node)

        elif isinstance(node, PrintNode):
            self._gen_print(node)

        else:
            raise ValueError(f"Unknown AST node in IR generation: {node}")

    # -------------------------
    # Data Declaration
    # data nums = [1,2,3]
    # IR: LIST [1,2,3] -> nums
    # -------------------------
    def _gen_data_decl(self, node: DataDeclarationNode):
        self.instructions.append(
            IRInstruction(
                op="LIST",
                arg1=node.values,   # literal Python list of ints
                arg2=None,
                result=node.name,
            )
        )

    # -------------------------
    # Assignment
    # big = select >5 from nums
    # total = sum from nums
    # -------------------------
    def _gen_assignment(self, node: AssignmentNode):
        # Generate IR for RHS expression and get result temp/var
        rhs_name = self._gen_expr(node.expr)

        # Assign to target variable
        self.instructions.append(
            IRInstruction(
                op="ASSIGN",
                arg1=rhs_name,
                arg2=None,
                result=node.target,
            )
        )

    # -------------------------
    # Expression dispatcher
    # -------------------------
    def _gen_expr(self, node) -> str:
        if isinstance(node, SelectQueryNode):
            return self._gen_select(node)
        if isinstance(node, FilterQueryNode):
            return self._gen_filter(node)
        if isinstance(node, AggregationNode):
            return self._gen_aggregation(node)
        raise ValueError(f"Invalid expression node in IR generation: {node}")

    # -------------------------
    # SELECT
    # select >5 from nums
    # select between 2 and 8 from nums
    # -------------------------
    def _gen_select(self, node: SelectQueryNode) -> str:
        temp = self.new_temp()
        cond = node.condition
        op = cond[0]

        if op == ">":
            self.instructions.append(
                IRInstruction(
                    op="FILTER_GT",
                    arg1=node.source,
                    arg2=cond[1],
                    result=temp,
                )
            )
        elif op == "<":
            self.instructions.append(
                IRInstruction(
                    op="FILTER_LT",
                    arg1=node.source,
                    arg2=cond[1],
                    result=temp,
                )
            )
        elif op == "=":
            self.instructions.append(
                IRInstruction(
                    op="FILTER_EQ",
                    arg1=node.source,
                    arg2=cond[1],
                    result=temp,
                )
            )
        elif op == "between":
            # cond = ("between", a, b)
            self.instructions.append(
                IRInstruction(
                    op="FILTER_BETWEEN",
                    arg1=node.source,
                    arg2=(cond[1], cond[2]),  # store bounds as tuple
                    result=temp,
                )
            )
        else:
            raise ValueError(f"Unknown select condition operator '{op}'")

        return temp

    # -------------------------
    # FILTER
    # filter even from nums
    # filter odd from nums
    # -------------------------
    def _gen_filter(self, node: FilterQueryNode) -> str:
        temp = self.new_temp()
        if node.mode == "even":
            op = "FILTER_EVEN"
        elif node.mode == "odd":
            op = "FILTER_ODD"
        else:
            raise ValueError(f"Unknown filter mode '{node.mode}'")

        self.instructions.append(
            IRInstruction(
                op=op,
                arg1=node.source,
                arg2=None,
                result=temp,
            )
        )
        return temp

    # -------------------------
    # Aggregations
    # sum from nums  →  AGG_SUM nums -> _t
    # max from nums  →  AGG_MAX nums -> _t
    # -------------------------
    def _gen_aggregation(self, node: AggregationNode) -> str:
        temp = self.new_temp()

        mapping = {
            "sum": "AGG_SUM",
            "max": "AGG_MAX",
            "min": "AGG_MIN",
            "count": "AGG_COUNT",
        }

        if node.func not in mapping:
            raise ValueError(f"Unknown aggregation function '{node.func}'")

        op = mapping[node.func]

        self.instructions.append(
            IRInstruction(
                op=op,
                arg1=node.source,
                arg2=None,
                result=temp,
            )
        )
        return temp

    # -------------------------
    # Print
    # print big  →  PRINT big
    # -------------------------
    def _gen_print(self, node: PrintNode):
        self.instructions.append(
            IRInstruction(
                op="PRINT",
                arg1=node.target,
                arg2=None,
                result=None,
            )
        )
