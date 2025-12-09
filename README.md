# MiniQuery Compiler

A small end-to-end compiler for a custom domain-specific language (**MiniQuery**) built for the **CS4031 – Compiler Construction** course.

The project implements **all six major compiler phases**:

1. Lexical Analysis  
2. Syntax Analysis  
3. Semantic Analysis  
4. Intermediate Code Generation  
5. Optimization  
6. Code Generation / Execution

Everything is done in **Python** and demonstrated through multiple `.mq` test files.

---

## 1. MiniQuery Language Overview

**MiniQuery** is a tiny DSL for performing simple operations on integer lists:

- Declare lists of integers  
- Select elements based on a condition  
- Filter even/odd elements  
- Apply aggregations (sum, max, min, count)  
- Assign query results to variables  
- Print values

### Example Program

```mq
data nums = [1,2,3,4,10,15]

big = select >5 from nums
evens = filter even from nums
total = sum from nums

print big
print evens
print total
```
### Supported Features

* **Data declaration**

  ```mq
  data nums = [1,2,3,4]
  ```

* **Selection queries**

  ```mq
  select >5 from nums
  select <3 from nums
  select =10 from nums
  select between 2 and 8 from nums
  ```

* **Filters**

  ```mq
  filter even from nums
  filter odd from nums
  ```

* **Aggregations**

  ```mq
  sum from nums
  max from nums
  min from nums
  count from nums
  ```

* **Assignments**

  ```mq
  result = select >5 from nums
  total = sum from nums
  ```

* **Print**

  ```mq
  print result
  ```

---

## 2. Project Structure

```text
MiniQueryCompiler/
  README.md

  src/
    lexer.py          # Lexical analysis
    parser.py         # Recursive-descent parser + AST
    semantic.py       # Symbol table + semantic checks
    ir_generator.py   # Intermediate representation (3-address code style)
    optimizer.py      # Simple optimizations (constant folding, DCE, copy prop)
    codegen.py        # IR execution engine (interpreter)
    ast_pretty.py     # Pretty-print tree for syntax analysis
    main.py           # Entry point: runs pipeline on test files / single file

  tests/
    test1.mq
    test2.mq
    test3.mq
    test4.mq
    test5.mq
    test6.mq
```

---

## 3. Implementation Details

### 3.1 Lexical Analysis (`lexer.py`)

* Implemented using Python `re` module.
* Produces `Token(type, value, line, column)` objects.
* Handles:

  * Keywords: `data, select, filter, sum, max, min, count, between, from, even, odd, print, and`
  * Identifiers: `[A-Za-z_][A-Za-z0-9_]*`
  * Numbers: `[0-9]+`
  * Symbols: `[ ] , > < =`
  * Comments: `# ...` (ignored)
  * Whitespace: ignored

### 3.2 Syntax Analysis (`parser.py`)

* Recursive-descent parser over a clean CFG.
* Builds an AST with node types:

  * `ProgramNode`
  * `DataDeclarationNode`
  * `AssignmentNode`
  * `SelectQueryNode`
  * `FilterQueryNode`
  * `AggregationNode`
  * `PrintNode`
* `ast_pretty.py` prints a **tree view** of the syntax:

  ```text
  Program
   ├── DataDeclaration(nums [1,2,3,4,10,15])
   ├── Assignment
   │   ├── TARGET: big
   │   └── SelectQuery
   │       ├── condition: ('>', 5)
   │       └── source: nums
   ├── ...
  ```

### 3.3 Semantic Analysis (`semantic.py`)

* Builds a **symbol table**:

  ```text
  name, type, element_type, size
  nums  : list<int>, elem=int, size=6
  big   : list<int>
  evens : list<int>
  total : int
  ```

* Checks:

  * Use of undeclared variables
  * Queries only on `list<int>`
  * Aggregations return `int`
  * Consistent assignment types

* Annotates AST nodes with `inferred_type` for later phases.

### 3.4 Intermediate Code Generation (`ir_generator.py`)

* Generates a simple IR with `IRInstruction(op, arg1, arg2, result)`.
* Example for:

  ```mq
  big = select >5 from nums
  ```

  IR:

  ```text
  LIST [1,2,3,4,10,15] -> nums
  FILTER_GT nums, 5 -> _t1
  ASSIGN _t1 -> big
  ```

### 3.5 Optimization (`optimizer.py`)

Implements basic optimizations:

* **Constant folding**

  * If a `LIST` is constant and filters are applied, results are computed at compile time.

* **Copy propagation**

  * Simple mapping `_t1 -> x` and replacing uses where possible.

* **Dead code elimination**

  * Assignments to values that are never used are removed.

### 3.6 Code Generation / Execution (`codegen.py`)

* Interprets IR sequentially using a Python `env` dictionary.
* Supports:

  * `LIST`
  * `ASSIGN`
  * `FILTER_GT / FILTER_LT / FILTER_EQ / FILTER_BETWEEN`
  * `FILTER_EVEN / FILTER_ODD`
  * `AGG_SUM / AGG_MAX / AGG_MIN / AGG_COUNT`
  * `PRINT`
* Produces final program output (lists and integers).

---

## 4. How to Run

### Requirements

* Python 3.8+ (any recent 3.x is fine)
* No external libraries needed

### Run all test cases

From project root:

```bash
python src/main.py
```

`main.py` will automatically execute:

* `tests/test1.mq` … `tests/test6.mq`

For each file it prints:

1. Source code
2. Token stream (Lexical Analysis)
3. Syntax tree summary (number of statements + pretty AST)
4. Symbol table (Semantic Analysis)
5. Original IR
6. Optimized IR
7. Final program output

### Run a single `.mq` file

```bash
python src/main.py tests/test3.mq
```

---

## 5. Test Files Summary

* `test1.mq` – basic select/filter/sum on `nums`
* `test2.mq` – `<` condition, odd filter, `max`
* `test3.mq` – `=` condition, `count` on base and derived list
* `test4.mq` – `between a and b`, `min` on base and selected list
* `test5.mq` – multiple datasets (`a`, `b`), mixed queries
* `test6.mq` – chained operations (`filter` → `select` → `sum` + `count`)

Each test exercises different language constructs and compiler phases.

---

## 6. Example Output (Short)

For `tests/test1.mq`:

```text
--- Lexical Analysis (Tokens) ---
1:1  DATA        'data'
1:6  ID          'nums'
...

--- Syntax Analysis (Parsing) ---
Parsing successful. Number of statements: 7

--- Syntax Tree (Pretty AST) ---
Program
 ├── DataDeclaration(nums [1,2,3,4,10,15])
 ├── Assignment
 │   ├── TARGET: big
 │   └── SelectQuery
 │       ├── condition: ('>', 5)
 │       └── source: nums
 ...

--- Semantic Analysis (Symbol Table) ---
  nums: type=list<int>, elem=int, size=6
  big: type=list<int>, elem=int, size=None
  evens: type=list<int>, elem=int, size=None
  total: type=int, elem=None, size=None

--- Intermediate Representation (Original IR) ---
00: LIST           [1, 2, 3, 4, 10, 15] None            -> 'nums'
01: FILTER_GT      'nums'          5               -> '_t1'
...

--- Optimized IR ---
00: LIST           [1, 2, 3, 4, 10, 15] None            -> 'nums'
01: LIST           [10, 15]        None            -> '_t1'
...

--- Program Output ---
[10, 15]
[2, 4, 10]
35
```

---

## 7. Limitations

* Only supports **integer lists** (no strings, no floats).
* No control flow (no if/else or loops).
* Single global scope only.

These are deliberate constraints to keep the language small but sufficient to demonstrate all compiler phases.

---

## 8. Authors

* Group members: *[Add names / roll numbers here]*
* Course: **CS4031 – Compiler Construction**
* Instructor: *[Add instructor’s name if needed]*

```

You can just paste this as `README.md` in the project root.

If you want, I can also give you a **shorter “viva script”** based on this README so you can verbally explain each phase in 1–2 lines.
```
