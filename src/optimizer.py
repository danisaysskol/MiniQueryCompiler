# src/optimizer.py

from typing import List
from ir_generator import IRInstruction


class Optimizer:
    """
    A simple optimizer that performs:
    - constant folding (LIST + filter ops on literals)
    - copy propagation
    - dead code elimination
    - redundant temp elimination
    """

    def optimize(self, ir: List[IRInstruction]) -> List[IRInstruction]:
        ir = self.constant_folding(ir)
        ir = self.copy_propagation(ir)
        ir = self.dead_code_elimination(ir)
        return ir

    # ------------------------------------------------------------
    # 1. CONSTANT FOLDING
    # If LIST + FILTER on literal list => evaluate filter at compile time.
    #
    # Example:
    #   LIST [1,2,3,10] -> nums
    #   FILTER_GT nums 5 -> _t1
    # becomes:
    #   LIST [1,2,3,10] -> nums
    #   LIST [10] -> _t1
    # ------------------------------------------------------------
    def constant_folding(self, ir: List[IRInstruction]) -> List[IRInstruction]:
        # Map variable name → literal list (if known constant)
        list_constants = {}

        new_ir = []

        for instr in ir:
            # LIST [x] → constant list
            if instr.op == "LIST":
                list_constants[instr.result] = instr.arg1
                new_ir.append(instr)
                continue

            # FILTER_GT, FILTER_LT, FILTER_EQ, FILTER_BETWEEN
            if instr.op.startswith("FILTER") and instr.arg1 in list_constants:
                raw_list = list_constants[instr.arg1]

                # Perform folding
                if instr.op == "FILTER_GT":
                    folded = [x for x in raw_list if x > instr.arg2]

                elif instr.op == "FILTER_LT":
                    folded = [x for x in raw_list if x < instr.arg2]

                elif instr.op == "FILTER_EQ":
                    folded = [x for x in raw_list if x == instr.arg2]

                elif instr.op == "FILTER_BETWEEN":
                    lo, hi = instr.arg2
                    folded = [x for x in raw_list if lo <= x <= hi]

                elif instr.op == "FILTER_EVEN":
                    folded = [x for x in raw_list if x % 2 == 0]

                elif instr.op == "FILTER_ODD":
                    folded = [x for x in raw_list if x % 2 != 0]

                else:
                    # unknown filter, leave unchanged
                    new_ir.append(instr)
                    continue

                # Record constant result
                list_constants[instr.result] = folded

                # Replace FILTER_* with LIST folded[]
                new_instr = IRInstruction(
                    op="LIST",
                    arg1=folded,
                    arg2=None,
                    result=instr.result
                )
                new_ir.append(new_instr)
                continue

            new_ir.append(instr)

        return new_ir

    # ------------------------------------------------------------
    # 2. COPY PROPAGATION
    # If we have:
    #   ASSIGN _t1 -> x
    # and _t1 is never used again, then replace x's use with _t1's value.
    # ------------------------------------------------------------
  
    def copy_propagation(self, ir: List[IRInstruction]) -> List[IRInstruction]:
        propagation_map = {}

        # Build simple map x -> _tK for ASSIGN _tK -> x
        for instr in ir:
            if instr.op == "ASSIGN" and isinstance(instr.arg1, str) and instr.arg1.startswith("_t"):
                propagation_map[instr.result] = instr.arg1

        # Apply propagation
        new_ir = []
        for instr in ir:
            arg1 = instr.arg1
            arg2 = instr.arg2

            if isinstance(arg1, str):
                arg1 = propagation_map.get(arg1, arg1)
            if isinstance(arg2, str):
                arg2 = propagation_map.get(arg2, arg2)

            new_instr = IRInstruction(
                op=instr.op,
                arg1=arg1,
                arg2=arg2,
                result=instr.result
            )
            new_ir.append(new_instr)

        return new_ir

    # ------------------------------------------------------------
    # 3. DEAD CODE ELIMINATION
    # If a temp variable OR a variable is never used, remove its assignment.
    # ------------------------------------------------------------
    def dead_code_elimination(self, ir: List[IRInstruction]) -> List[IRInstruction]:
        used = set()

        # First pass: collect all used variables
        for instr in ir:
            if isinstance(instr.arg1, str):
                used.add(instr.arg1)
            if isinstance(instr.arg2, str):
                used.add(instr.arg2)

        # Second pass: remove instructions that define unused values
        new_ir = []
        for instr in ir:
            if instr.result is not None and instr.result not in used:
                # This assignment is dead
                continue
            new_ir.append(instr)

        return new_ir
