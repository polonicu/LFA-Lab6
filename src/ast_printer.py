"""
AST pretty-printer.

Produces a readable indented tree representation of any ASTNode,
useful for debugging and for the demo output shown in the README.
"""
from __future__ import annotations

from src.ast_nodes import (
    ASTNode, Program, Block,
    IntegerLiteral, FloatLiteral, StringLiteral, BooleanLiteral, Identifier,
    BinaryOp, UnaryOp, Assignment, FunctionCall, BuiltinCall,
    ExpressionStatement, LetStatement, ReturnStatement,
    IfStatement, WhileStatement, ForStatement, FunctionDef,
)


def print_ast(node: ASTNode, indent: int = 0) -> str:
    """Return a multi-line string representation of the subtree rooted at node."""
    pad = "  " * indent
    lines: list[str] = []

    if isinstance(node, Program):
        lines.append(f"{pad}Program")
        for stmt in node.statements:
            lines.append(print_ast(stmt, indent + 1))

    elif isinstance(node, FunctionDef):
        params = ", ".join(node.params)
        lines.append(f"{pad}FunctionDef '{node.name}'({params})")
        lines.append(print_ast(node.body, indent + 1))

    elif isinstance(node, Block):
        lines.append(f"{pad}Block")
        for stmt in node.statements:
            lines.append(print_ast(stmt, indent + 1))

    elif isinstance(node, LetStatement):
        lines.append(f"{pad}Let '{node.name}'")
        lines.append(print_ast(node.initializer, indent + 1))

    elif isinstance(node, ReturnStatement):
        lines.append(f"{pad}Return")
        lines.append(print_ast(node.value, indent + 1))

    elif isinstance(node, IfStatement):
        lines.append(f"{pad}If")
        lines.append(f"{pad}  condition:")
        lines.append(print_ast(node.condition, indent + 2))
        lines.append(f"{pad}  then:")
        lines.append(print_ast(node.then_branch, indent + 2))
        if node.else_branch is not None:
            lines.append(f"{pad}  else:")
            lines.append(print_ast(node.else_branch, indent + 2))

    elif isinstance(node, WhileStatement):
        lines.append(f"{pad}While")
        lines.append(f"{pad}  condition:")
        lines.append(print_ast(node.condition, indent + 2))
        lines.append(f"{pad}  body:")
        lines.append(print_ast(node.body, indent + 2))

    elif isinstance(node, ForStatement):
        lines.append(f"{pad}For")
        lines.append(f"{pad}  init:")
        lines.append(print_ast(node.init, indent + 2))
        lines.append(f"{pad}  condition:")
        lines.append(print_ast(node.condition, indent + 2))
        lines.append(f"{pad}  update:")
        lines.append(print_ast(node.update, indent + 2))
        lines.append(f"{pad}  body:")
        lines.append(print_ast(node.body, indent + 2))

    elif isinstance(node, ExpressionStatement):
        lines.append(f"{pad}ExprStmt")
        lines.append(print_ast(node.expression, indent + 1))

    elif isinstance(node, Assignment):
        lines.append(f"{pad}Assign '{node.name}'")
        lines.append(print_ast(node.value, indent + 1))

    elif isinstance(node, BinaryOp):
        lines.append(f"{pad}BinaryOp '{node.operator}'")
        lines.append(print_ast(node.left, indent + 1))
        lines.append(print_ast(node.right, indent + 1))

    elif isinstance(node, UnaryOp):
        lines.append(f"{pad}UnaryOp '{node.operator}'")
        lines.append(print_ast(node.operand, indent + 1))

    elif isinstance(node, FunctionCall):
        lines.append(f"{pad}Call '{node.name}'")
        for arg in node.arguments:
            lines.append(print_ast(arg, indent + 1))

    elif isinstance(node, BuiltinCall):
        lines.append(f"{pad}Builtin '{node.function}'")
        lines.append(print_ast(node.argument, indent + 1))

    elif isinstance(node, Identifier):
        lines.append(f"{pad}Identifier '{node.name}'")

    elif isinstance(node, IntegerLiteral):
        lines.append(f"{pad}Integer {node.value}")

    elif isinstance(node, FloatLiteral):
        lines.append(f"{pad}Float {node.value}")

    elif isinstance(node, StringLiteral):
        lines.append(f"{pad}String {node.value!r}")

    elif isinstance(node, BooleanLiteral):
        lines.append(f"{pad}Boolean {node.value}")

    else:
        lines.append(f"{pad}{node!r}")

    return "\n".join(lines)