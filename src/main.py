# src/main.py

import os
import sys

from lexer import Lexer, LexerError
from parser import Parser, ParserError
from semantic import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from optimizer import Optimizer
from codegen import CodeGenerator, RuntimeErrorMiniQuery
from ast_pretty import pretty



TEST_FILES = [
    "tests/test1.mq",
    # "tests/test2.mq",
    # "tests/test3.mq",
    # "tests/test4.mq",
    # "tests/test5.mq",
    # "tests/test6.mq",
]


def run_single_file(path: str):
    print("=" * 80)
    print(f"Running file: {path}")
    print("=" * 80)

    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, "r") as f:
        source_code = f.read()

    print("\n--- Source Code ---")
    print(source_code.strip())

    # 1) Lexical analysis
    print("\n--- Lexical Analysis (Tokens) ---")
    try:
        tokens = Lexer(source_code).tokenize()
    except LexerError as e:
        print("Lexer error:", e)
        return

    for tok in tokens:
        print(f"{tok.line}:{tok.column}  {tok.type:10}  {tok.value!r}")

    # 2) Parsing
    print("\n--- Syntax Analysis (Parsing) ---")
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        print("Parsing successful. Number of statements:", len(ast.statements))
        print("\n--- Syntax Tree (Pretty AST) ---")
        print(pretty(ast))

    except ParserError as e:
        print("Parser error:", e)
        return

    # 3) Semantic analysis
    print("\n--- Semantic Analysis (Symbol Table) ---")
    analyzer = SemanticAnalyzer()
    try:
        symbols = analyzer.analyze(ast)
    except SemanticError as e:
        print("Semantic error:", e)
        return

    if not symbols:
        print("No symbols.")
    else:
        for name, sym in symbols.items():
            print(f"  {name}: type={sym.type}, elem={sym.element_type}, size={sym.size}")

    # 4) IR generation
    print("\n--- Intermediate Representation (Original IR) ---")
    irgen = IRGenerator()
    ir = irgen.generate(ast)
    for i, instr in enumerate(ir):
        print(f"{i:02}: {instr.op:14} {repr(instr.arg1):15} {repr(instr.arg2):15} -> {repr(instr.result)}")

    # 5) Optimization
    print("\n--- Optimized IR ---")
    opt = Optimizer()
    optimized_ir = opt.optimize(ir)
    for i, instr in enumerate(optimized_ir):
        print(f"{i:02}: {instr.op:14} {repr(instr.arg1):15} {repr(instr.arg2):15} -> {repr(instr.result)}")

    # 6) Code generation / execution
    print("\n--- Program Output ---")
    codegen = CodeGenerator()
    try:
        codegen.run(optimized_ir)
    except RuntimeErrorMiniQuery as e:
        print("Runtime error:", e)

    print("\n")  # extra spacing between tests


def main():
    # If user gives a specific file: python src/main.py tests/test3.mq
    if len(sys.argv) > 1:
        run_single_file(sys.argv[1])
    else:
        # Run all 6 predefined tests
        for path in TEST_FILES:
            run_single_file(path)


if __name__ == "__main__":
    main()
