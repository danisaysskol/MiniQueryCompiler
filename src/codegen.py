# src/codegen.py

from typing import List, Dict, Any
from ir_generator import IRInstruction


class RuntimeErrorMiniQuery(Exception):
    pass


class CodeGenerator:
    """
    Executes the IR instructions produced by IRGenerator.
    env: maps variable names (including temps like _t1) to Python values
         (either list[int] or int).
    """

    def __init__(self):
        self.env: Dict[str, Any] = {}

    def run(self, ir: List[IRInstruction]):
        """
        Execute IR sequentially.
        """
        self.env.clear()

        for instr in ir:
            op = instr.op

            if op == "LIST":
                self._exec_list(instr)

            elif op == "ASSIGN":
                self._exec_assign(instr)

            elif op in ("FILTER_GT", "FILTER_LT", "FILTER_EQ",
                        "FILTER_BETWEEN", "FILTER_EVEN", "FILTER_ODD"):
                self._exec_filter(instr)

            elif op in ("AGG_SUM", "AGG_MAX", "AGG_MIN", "AGG_COUNT"):
                self._exec_aggregation(instr)

            elif op == "PRINT":
                self._exec_print(instr)

            else:
                raise RuntimeErrorMiniQuery(f"Unknown IR operation '{op}'")

    # -------------------------
    # LIST [values] -> name
    # -------------------------
    def _exec_list(self, instr: IRInstruction):
        values = instr.arg1
        if not isinstance(values, list):
            raise RuntimeErrorMiniQuery("LIST instruction expects a list in arg1")

        # store a copy to avoid accidental mutation
        self.env[instr.result] = list(values)

    # -------------------------
    # ASSIGN src -> dest
    # -------------------------
    def _exec_assign(self, instr: IRInstruction):
        src = instr.arg1
        dest = instr.result

        if src not in self.env:
            raise RuntimeErrorMiniQuery(f"ASSIGN from unknown variable '{src}'")

        self.env[dest] = self.env[src]

    # -------------------------
    # FILTER_* operations
    # -------------------------
    def _exec_filter(self, instr: IRInstruction):
        src_name = instr.arg1
        if src_name not in self.env:
            raise RuntimeErrorMiniQuery(f"FILTER from unknown variable '{src_name}'")

        src_val = self.env[src_name]
        if not isinstance(src_val, list):
            raise RuntimeErrorMiniQuery(f"FILTER expects list, got {type(src_val)}")

        op = instr.op
        result_name = instr.result

        if op == "FILTER_GT":
            threshold = instr.arg2
            result = [x for x in src_val if x > threshold]

        elif op == "FILTER_LT":
            threshold = instr.arg2
            result = [x for x in src_val if x < threshold]

        elif op == "FILTER_EQ":
            value = instr.arg2
            result = [x for x in src_val if x == value]

        elif op == "FILTER_BETWEEN":
            lo, hi = instr.arg2
            result = [x for x in src_val if lo <= x <= hi]

        elif op == "FILTER_EVEN":
            result = [x for x in src_val if x % 2 == 0]

        elif op == "FILTER_ODD":
            result = [x for x in src_val if x % 2 != 0]

        else:
            raise RuntimeErrorMiniQuery(f"Unknown filter operation '{op}'")

        self.env[result_name] = result

    # -------------------------
    # Aggregations
    # -------------------------
    def _exec_aggregation(self, instr: IRInstruction):
        src_name = instr.arg1
        if src_name not in self.env:
            raise RuntimeErrorMiniQuery(f"AGG from unknown variable '{src_name}'")

        src_val = self.env[src_name]
        if not isinstance(src_val, list):
            raise RuntimeErrorMiniQuery(f"AGG expects list, got {type(src_val)}")

        op = instr.op
        result_name = instr.result

        if op == "AGG_SUM":
            value = sum(src_val)
        elif op == "AGG_MAX":
            value = max(src_val) if src_val else None
        elif op == "AGG_MIN":
            value = min(src_val) if src_val else None
        elif op == "AGG_COUNT":
            value = len(src_val)
        else:
            raise RuntimeErrorMiniQuery(f"Unknown aggregation operation '{op}'")

        self.env[result_name] = value

    # -------------------------
    # PRINT
    # -------------------------
    def _exec_print(self, instr: IRInstruction):
        var_name = instr.arg1
        if var_name not in self.env:
            raise RuntimeErrorMiniQuery(f"PRINT of unknown variable '{var_name}'")

        value = self.env[var_name]
        print(value)
