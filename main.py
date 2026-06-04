"""
Lab 4: Parser & AST demo.
Run from the project root:  python main.py
"""
from src.lexer import Lexer
from src.parser import Parser
from src.ast_printer import print_ast


DEMOS: list[tuple[str, str]] = [
    # ------------------------------------------------------------------ 1
    (
        "Arithmetic expression",
        "2 + 3 * 4 - 1\n",
    ),
    # ------------------------------------------------------------------ 2
    (
        "Variable declaration",
        "let x = 10\nlet y = x * 2 + 1\n",
    ),
    # ------------------------------------------------------------------ 3
    (
        "Function definition and call",
        """\
fn distance(x1, y1, x2, y2) {
    let dx = x2 - x1
    let dy = y2 - y1
    return sqrt(dx^2 + dy^2)
}
let result = distance(0.0, 0.0, 3.0, 4.0)
""",
    ),
    # ------------------------------------------------------------------ 4
    (
        "If / else statement",
        """\
fn abs_val(n) {
    if (n < 0) {
        return -n
    } else {
        return n
    }
}
""",
    ),
    # ------------------------------------------------------------------ 5
    (
        "While loop with compound condition",
        """\
let i = 0
let sum = 0
while (i < 10) {
    sum = sum + i
    i = i + 1
}
""",
    ),
]


def run_demo(title: str, source: str) -> None:
    separator = "-" * 60
    print(separator)
    print(f"Demo: {title}")
    print(separator)
    print("[source]")
    print(source.rstrip())
    print()

    tokens = Lexer(source).tokenize()
    print("[tokens]")
    for tok in tokens:
        print(f"  {tok}")
    print()

    ast = Parser(tokens).parse()
    print("[AST]")
    print(print_ast(ast))
    print()


def main() -> None:
    print("=" * 60)
    print("  Lab 4 -- Parser & Abstract Syntax Tree")
    print("=" * 60)
    print()
    for title, source in DEMOS:
        run_demo(title, source)


if __name__ == "__main__":
    main()