# src/main.py

from lexer import Lexer, LexerError
from parser import Parser, ParserError
from semantic import SemanticAnalyzer, SemanticError
from ir_generator import IRGenerator
from optimizer import Optimizer
from codegen import CodeGenerator, RuntimeErrorMiniQuery


def main():
    # TODO: later: read from file via CLI. For now, embedded demo.
    source_code = """
    data nums = [1,2,3,4,10,15]
    total = sum from nums
    print total
    """

    # 1) Lexical analysis
    try:
        tokens = Lexer(source_code).tokenize()
        # printing the tokens
        for token in tokens:
            print(f"{token.line}:{token.column}  {token.type:10}  {token.value!r}")
    except LexerError as e:
        print("Lexer error:", e)
        return

    # 2) Parsing
    try:
        parser = Parser(tokens)
        ast = parser.parse()

        # printing the parsing result
        print("\nParsed AST:")
        
    except ParserError as e:
        print("Parser error:", e)
        return

    # 3) Semantic analysis
    analyzer = SemanticAnalyzer()
    try:
        symbols = analyzer.analyze(ast)
    except SemanticError as e:
        print("Semantic error:", e)
        return

    print("Semantic analysis successful.")
    print("Symbol table:")
    for name, sym in symbols.items():
        print(f"  {name}: {sym.type}, elem={sym.element_type}, size={sym.size}")

    # 4) IR generation
    irgen = IRGenerator()
    ir = irgen.generate(ast)

    print("\nOriginal IR:")
    for i, instr in enumerate(ir):
        print(f"{i:02}: {instr.op}  {instr.arg1!r}  {instr.arg2!r}  -> {instr.result!r}")

    # 5) Optimization
    opt = Optimizer()
    optimized_ir = opt.optimize(ir)

    print("\nOptimized IR:")
    for i, instr in enumerate(optimized_ir):
        print(f"{i:02}: {instr.op}  {instr.arg1!r}  {instr.arg2!r}  -> {instr.result!r}")

    # 6) Code generation / execution
    codegen = CodeGenerator()
    print("\nProgram output:")
    try:
        codegen.run(optimized_ir)
    except RuntimeErrorMiniQuery as e:
        print("Runtime error:", e)


if __name__ == "__main__":
    main()
