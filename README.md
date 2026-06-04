# Laboratory Work 4: Parser and Abstract Syntax Tree

**Course:** Formal Languages and Finite Automata  
**Author:** Turcanu Nicolae

---

## Table of Contents

1. [Theory](#theory)
2. [Objectives](#objectives)
3. [The Language](#the-language)
4. [Implementation](#implementation)
   - [Project Structure](#project-structure)
   - [TokenType and the Lexer](#tokentype-and-the-lexer)
   - [AST Node Hierarchy](#ast-node-hierarchy)
   - [The Parser](#the-parser)
   - [AST Printer](#ast-printer)
5. [How the Parser Works](#how-the-parser-works)
   - [Recursive Descent](#recursive-descent)
   - [Operator Precedence Table](#operator-precedence-table)
   - [Statement Parsing](#statement-parsing)
   - [Expression Parsing](#expression-parsing)
   - [Error Handling](#error-handling)
6. [Running the Code](#running-the-code)
7. [Example Output](#example-output)
8. [Tests](#tests)
9. [Conclusions](#conclusions)
10. [References](#references)

---

## Theory

**Parsing** (also called syntactic analysis) is the second stage in a typical compiler or interpreter pipeline, immediately following lexical analysis.  Where the lexer converts raw characters into a flat sequence of tokens, the parser imposes structure on that sequence by recognising the grammatical rules of the language.

The canonical output of a parser is a **parse tree** (also called a concrete syntax tree), which mirrors the grammar rules exactly and therefore contains a great deal of noise: brackets, commas, semicolons, and other punctuation that is necessary for disambiguation but carries no semantic weight.

An **Abstract Syntax Tree (AST)** strips away that noise.  Each node represents a meaningful construct: a binary operation, a variable declaration, a function definition.  The "abstract" in the name refers to the fact that several concrete syntactic details are absent from the tree.  For example, the parentheses in `(2 + 3) * 4` appear in the parse tree but are replaced in the AST by the tree's own structure: the `+` node becomes the left child of `*`, which already encodes the intended evaluation order.

ASTs are the standard internal representation used in real compilers (GCC's GIMPLE, Clang's AST, CPython's `ast` module) as well as in static analysis tools, code formatters, linters, and language servers.

---

## Objectives

1. Understand what parsing is and how it fits into the compilation pipeline.
2. Understand the concept of an Abstract Syntax Tree.
3. Extend the `TokenType` enum from Lab 3 with regex-based categorisation.
4. Design and implement an AST node hierarchy for the scripting language processed in Lab 3.
5. Implement a recursive-descent parser that transforms the token stream into an AST.

---

## The Language

This lab continues working with the same small expression-oriented scripting language introduced in Lab 3.  The language supports:

- Integer and float literals (`42`, `3.14`, `1.5e-3`)
- String literals with escape sequences (`"hello\nworld"`)
- Boolean literals (`true`, `false`)
- Identifiers matching `[a-zA-Z_]\w*`
- Reserved keywords: `if`, `else`, `while`, `for`, `return`, `let`, `fn`, `and`, `or`, `not`
- Built-in math functions: `sin`, `cos`, `tan`, `sqrt`, `abs`
- Arithmetic operators: `+`, `-`, `*`, `/`, `%`, `^`
- Comparison operators: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Assignment: `=`
- Delimiters: `(`, `)`, `{`, `}`, `[`, `]`, `,`, `;`, `:`, `.`
- Single-line comments starting with `#`

A representative program in this language:

```
# Euclidean distance
fn distance(x1, y1, x2, y2) {
    let dx = x2 - x1
    let dy = y2 - y1
    return sqrt(dx^2 + dy^2)
}

let result = distance(0.0, 0.0, 3.0, 4.0)
```

---

## Implementation

### Project Structure

```
lab4/
    main.py                  # entry point: python main.py
    src/
        __init__.py
        token_type.py        # TokenType enum + regex patterns + keyword map
        token.py             # Token dataclass
        lexer.py             # Lexer class (from Lab 3)
        ast_nodes.py         # all AST node dataclasses
        parser.py            # recursive-descent Parser class
        ast_printer.py       # indented pretty-printer for AST nodes
    tests/
        __init__.py
        test_parser.py       # 39 pytest tests
```

### TokenType and the Lexer

`src/token_type.py` defines the `TokenType` enum whose members cover every token category the language can produce.  Each category is matched by a compiled regular expression stored in `TOKEN_PATTERNS`, a list of `(TokenType, re.Pattern)` pairs.  The lexer iterates this list in priority order and calls `pattern.match(source, pos)` at the current position, which anchors the match at `pos` without requiring a full scan.

Resolving an `IDENTIFIER` token to a keyword or boolean is a separate step: after the regex match the lexer looks the lexeme up in `KEYWORD_MAP` and replaces the token type if a match is found.  This keeps the grammar patterns clean and avoids a combinatorial explosion of keyword-specific patterns.

### AST Node Hierarchy

All nodes inherit from `ASTNode`, a plain marker class.  Every concrete node is a Python `dataclass`, which gives automatic `__init__`, `__repr__`, and `__eq__` with no boilerplate.

The hierarchy is organised into three groups:

**Literals** hold a single Python value:

| Node | Field | Example |
|------|-------|---------|
| `IntegerLiteral` | `value: int` | `42` |
| `FloatLiteral` | `value: float` | `3.14` |
| `StringLiteral` | `value: str` | `"hi"` |
| `BooleanLiteral` | `value: bool` | `true` |

**Expressions** represent operations and references:

| Node | Fields | Example |
|------|--------|---------|
| `Identifier` | `name: str` | `x` |
| `BinaryOp` | `operator, left, right` | `a + b` |
| `UnaryOp` | `operator, operand` | `-x` |
| `Assignment` | `name, value` | `x = 5` |
| `FunctionCall` | `name, arguments` | `f(1, 2)` |
| `BuiltinCall` | `function, argument` | `sqrt(9)` |

**Statements** represent control flow and declarations:

| Node | Fields | Example |
|------|--------|---------|
| `LetStatement` | `name, initializer` | `let x = 10` |
| `ReturnStatement` | `value` | `return x` |
| `ExpressionStatement` | `expression` | `foo()` |
| `Block` | `statements: list` | `{ ... }` |
| `IfStatement` | `condition, then_branch, else_branch` | `if (...) { }` |
| `WhileStatement` | `condition, body` | `while (...) { }` |
| `ForStatement` | `init, condition, update, body` | `for (...) { }` |
| `FunctionDef` | `name, params, body` | `fn f(a) { }` |

The top-level `Program` node holds a list of statements and is the root of every AST.

### The Parser

`src/parser.py` implements a hand-written recursive-descent parser.  It consumes the flat token list produced by `Lexer.tokenize()` and returns a `Program` node.

The parser maintains a single integer cursor `_pos` into the token list and exposes four low-level primitives:

- `_peek()` returns the current token without advancing.
- `_advance()` returns and consumes the current token.
- `_consume(expected)` advances and raises `ParseError` if the type does not match.
- `_match(*types)` advances and returns `True` if the current token matches any of the given types.

Every grammar rule maps to exactly one method.

### AST Printer

`src/ast_printer.py` exports a single function `print_ast(node, indent)` that returns a multi-line string showing the tree with two-space indentation.  It uses `isinstance` dispatch on every known node type.  The printer is used in the demo (`main.py`) and is useful during debugging.

---

## How the Parser Works

### Recursive Descent

A recursive-descent parser encodes the grammar directly as a set of mutually recursive functions.  Each function is responsible for recognising one grammar rule and returning the corresponding AST node.  When a rule refers to another rule, the first function calls the second.

The technique is straightforward to implement, easy to debug, and produces clear error messages because each function knows exactly what it was trying to parse when it failed.

### Operator Precedence Table

Operator precedence is encoded implicitly by the call hierarchy.  A lower-precedence rule calls a higher-precedence rule as its operand, so higher-precedence operators bind tighter.

| Level | Operators | Associativity | Parser method |
|-------|-----------|---------------|---------------|
| 1 (lowest) | `=` (assignment) | right | `_assignment` |
| 2 | `or` | left | `_logical_or` |
| 3 | `and` | left | `_logical_and` |
| 4 | `==` `!=` | left | `_equality` |
| 5 | `<` `>` `<=` `>=` | left | `_comparison` |
| 6 | `+` `-` | left | `_term` |
| 7 | `*` `/` `%` | left | `_factor` |
| 8 | `^` (power) | right | `_power` |
| 9 | `not` `-` (unary) | right | `_unary` |
| 10 (highest) | `f(...)` | left | `_call` |

Because `_term` calls `_factor` and `_factor` calls `_power`, a multiplication always binds its operands before addition gets a chance to consume them.  Parenthesised sub-expressions re-enter at the lowest precedence level (`_expression`), which is how grouping overrides precedence.

Right-associativity (assignment, power) is implemented by having the parsing function call itself recursively for the right-hand operand instead of looping:

```python
def _power(self) -> ASTNode:
    base = self._unary()
    if self._peek().type == TokenType.CARET:
        op = self._advance().value
        exp = self._power()          # recursive call: right-associative
        return BinaryOp(operator=op, left=base, right=exp)
    return base
```

Left-associativity uses an iterative `while` loop:

```python
def _term(self) -> ASTNode:
    node = self._factor()
    while self._peek().type in (TokenType.PLUS, TokenType.MINUS):
        op = self._advance().value
        right = self._factor()
        node = BinaryOp(operator=op, left=node, right=right)   # accumulate left
    return node
```

### Statement Parsing

`_statement` is the dispatch point for all statement types.  It peeks at the current token and forwards to the appropriate handler:

```
FN         -> _fn_def
LET        -> _let_stmt
RETURN     -> _return_stmt
IF         -> _if_stmt
WHILE      -> _while_stmt
FOR        -> _for_stmt
anything   -> _expr_stmt
```

Blocks are delimited by `{` and `}`.  The parser consumes the opening brace, then loops collecting statements until it sees `}` or EOF.  Newlines inside blocks are skipped via `_skip_newlines()` before and after each statement so the language can be written in a line-sensitive style without requiring explicit semicolons.

### Expression Parsing

The expression hierarchy starts at `_expression`, which calls `_assignment`.  For most tokens this immediately delegates down the precedence chain to `_logical_or` and below.  The only special case is assignment: the parser uses a one-token look-ahead to check whether the current `IDENTIFIER` is followed by `ASSIGN` (`=`).  If so it consumes both, then calls `_assignment` recursively to parse the right-hand side.

Built-in calls (`sin`, `cos`, etc.) are handled in `_primary` because the built-in keyword tokens would otherwise be unrecognised there.  User-defined function calls are detected in `_primary` when an `IDENTIFIER` is immediately followed by `(`.

### Error Handling

`ParseError` is raised by `_consume` whenever the next token does not match the expected type.  It includes a human-readable message and the offending `Token` object (with line and column information).  The parser does not attempt recovery; it fails fast so that the caller always sees a clean exception rather than a partially-constructed or silently wrong tree.

---

## Running the Code

**Requirements:** Python 3.10 or newer (uses `match`-free dataclasses and `X | Y` union types in annotations; the `__future__` import handles Python 3.10).

```bash
# clone the repository and navigate to this lab
cd src/lab4

# run the demo (five annotated programs)
python main.py

# run the test suite
pytest tests/ -v
```

No third-party packages are required to run the parser or the demo.  `pytest` is the only dependency, needed only for the test suite.

---

## Example Output

Running `python main.py` prints five demos, each showing the source, the token list from the lexer, and the AST produced by the parser.

**Demo 1: arithmetic precedence**

```
source:  2 + 3 * 4 - 1

AST:
Program
  ExprStmt
    BinaryOp '-'
      BinaryOp '+'
        Integer 2
        BinaryOp '*'
          Integer 3
          Integer 4
      Integer 1
```

Multiplication binds before addition: `3 * 4` becomes a subtree that is the right child of `+`, which in turn is the left child of `-`.

**Demo 3: function definition with builtin call**

```
source:
  fn distance(x1, y1, x2, y2) {
      let dx = x2 - x1
      let dy = y2 - y1
      return sqrt(dx^2 + dy^2)
  }
  let result = distance(0.0, 0.0, 3.0, 4.0)

AST:
Program
  FunctionDef 'distance'(x1, y1, x2, y2)
    Block
      Let 'dx'
        BinaryOp '-'
          Identifier 'x2'
          Identifier 'x1'
      Let 'dy'
        BinaryOp '-'
          Identifier 'y2'
          Identifier 'y1'
      Return
        Builtin 'sqrt'
          BinaryOp '+'
            BinaryOp '^'
              Identifier 'dx'
              Integer 2
            BinaryOp '^'
              Identifier 'dy'
              Integer 2
  Let 'result'
    Call 'distance'
      Float 0.0
      Float 0.0
      Float 3.0
      Float 4.0
```

---

## Tests

The test suite in `tests/test_parser.py` contains 39 tests organised into classes by feature area.

```
tests/test_parser.py::TestLiterals             5 tests
tests/test_parser.py::TestArithmetic           6 tests
tests/test_parser.py::TestLogical              6 tests
tests/test_parser.py::TestLetStatement         3 tests
tests/test_parser.py::TestAssignment           1 test
tests/test_parser.py::TestFunctionDef          3 tests
tests/test_parser.py::TestIfStatement          2 tests
tests/test_parser.py::TestWhileStatement       1 test
tests/test_parser.py::TestFunctionCall         3 tests
tests/test_parser.py::TestBuiltinCall          3 tests
tests/test_parser.py::TestReturnStatement      1 test
tests/test_parser.py::TestProgram              2 tests
tests/test_parser.py::TestParseErrors          3 tests
```

All 39 tests pass.  Coverage spans literals, every operator precedence level, all statement forms, function definitions and calls, builtins, and three error cases that confirm `ParseError` is raised for malformed input.

---

## Conclusions

This lab extended the Lab 3 lexer with a full recursive-descent parser and an AST.

The key design decisions were:

1. **Dataclasses for AST nodes.** Using `@dataclass` eliminates boilerplate and gives each node a clean, inspectable representation with no extra code.

2. **Precedence via call depth.** Encoding operator precedence in the call hierarchy rather than in a lookup table keeps each parsing function short and makes the precedence rules immediately visible from the code structure.

3. **Right-associativity via recursion.** Power and assignment are made right-associative simply by having each function call itself rather than loop.  This is one of the elegances of recursive descent.

4. **Separate BuiltinCall node.** Distinguishing built-in math calls from user-defined function calls at the AST level makes it straightforward for a later compilation or evaluation stage to handle them differently (e.g. emit a CPU instruction for `sqrt` rather than a function call).

5. **Fail-fast error handling.** Raising `ParseError` immediately with line and column information makes debugging malformed input much easier than silent failure or error recovery.

The resulting AST is a clean, hierarchical representation of the source program that a subsequent evaluation or code generation stage could consume directly without re-parsing any text.

---

## References

[1] Parsing -- Wikipedia: https://en.wikipedia.org/wiki/Parsing  
[2] Abstract Syntax Tree -- Wikipedia: https://en.wikipedia.org/wiki/Abstract_syntax_tree  
[3] Crafting Interpreters, Robert Nystrom -- https://craftinginterpreters.com  
[4] LLVM Kaleidoscope Tutorial -- https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl02.html