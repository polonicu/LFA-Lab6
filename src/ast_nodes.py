"""
Abstract Syntax Tree node definitions.

Every node in the AST inherits from ASTNode.  Nodes are plain dataclasses
so they are easy to inspect, pretty-print, and traverse without needing to
import anything outside the standard library.

Grammar (informal):

    program        -> statement* EOF
    statement      -> fn_def | let_stmt | return_stmt | if_stmt
                    | while_stmt | for_stmt | expr_stmt
    fn_def         -> 'fn' IDENTIFIER '(' params ')' block
    let_stmt       -> 'let' IDENTIFIER '=' expression
    return_stmt    -> 'return' expression
    if_stmt        -> 'if' '(' expression ')' block ( 'else' block )?
    while_stmt     -> 'while' '(' expression ')' block
    for_stmt       -> 'for' '(' let_stmt ';' expression ';' expression ')' block
    block          -> '{' statement* '}'
    expr_stmt      -> expression NEWLINE
    expression     -> assignment
    assignment     -> IDENTIFIER '=' assignment | logical_or
    logical_or     -> logical_and ( 'or' logical_and )*
    logical_and    -> equality   ( 'and' equality  )*
    equality       -> comparison ( ( '==' | '!=' ) comparison )*
    comparison     -> term       ( ( '<' | '>' | '<=' | '>=' ) term )*
    term           -> factor     ( ( '+' | '-' ) factor )*
    factor         -> power      ( ( '*' | '/' | '%' ) power )*
    power          -> unary      ( '^' unary )*
    unary          -> ( 'not' | '-' ) unary | call
    call           -> primary ( '(' arguments ')' )*
    primary        -> INTEGER | FLOAT | STRING | BOOLEAN | IDENTIFIER
                    | '(' expression ')'
                    | builtin '(' expression ')'
    builtin        -> 'sin' | 'cos' | 'tan' | 'sqrt' | 'abs'
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class ASTNode:
    """Marker base class for all AST nodes."""

    def __repr__(self) -> str:  # pragma: no cover
        fields = ", ".join(
            f"{k}={v!r}" for k, v in self.__dict__.items()
        )
        return f"{self.__class__.__name__}({fields})"


# ---------------------------------------------------------------------------
# Literals
# ---------------------------------------------------------------------------

@dataclass
class IntegerLiteral(ASTNode):
    value: int


@dataclass
class FloatLiteral(ASTNode):
    value: float


@dataclass
class StringLiteral(ASTNode):
    value: str


@dataclass
class BooleanLiteral(ASTNode):
    value: bool


# ---------------------------------------------------------------------------
# Identifier reference
# ---------------------------------------------------------------------------

@dataclass
class Identifier(ASTNode):
    name: str


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

@dataclass
class BinaryOp(ASTNode):
    """Any binary expression: arithmetic, comparison, logical."""
    operator: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    """Unary prefix expression: 'not' or unary '-'."""
    operator: str
    operand: ASTNode


@dataclass
class Assignment(ASTNode):
    """Variable assignment: name = expr."""
    name: str
    value: ASTNode


@dataclass
class FunctionCall(ASTNode):
    """User-defined or built-in function call: name(arg1, arg2, ...)."""
    name: str
    arguments: list[ASTNode] = field(default_factory=list)


@dataclass
class BuiltinCall(ASTNode):
    """Builtin math call: sin(x), cos(x), etc.  Kept separate for clarity."""
    function: str
    argument: ASTNode


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

@dataclass
class ExpressionStatement(ASTNode):
    """A statement that is just an expression (e.g. a bare function call)."""
    expression: ASTNode


@dataclass
class LetStatement(ASTNode):
    """Variable declaration: let name = expr."""
    name: str
    initializer: ASTNode


@dataclass
class ReturnStatement(ASTNode):
    value: ASTNode


@dataclass
class Block(ASTNode):
    """A brace-delimited sequence of statements."""
    statements: list[ASTNode] = field(default_factory=list)


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_branch: Block
    else_branch: Block | None = None


@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body: Block


@dataclass
class ForStatement(ASTNode):
    """for (init; condition; update) { body }"""
    init: LetStatement
    condition: ASTNode
    update: ASTNode
    body: Block


@dataclass
class FunctionDef(ASTNode):
    name: str
    params: list[str]
    body: Block


# ---------------------------------------------------------------------------
# Top-level program
# ---------------------------------------------------------------------------

@dataclass
class Program(ASTNode):
    """Root node; holds the list of top-level statements."""
    statements: list[ASTNode] = field(default_factory=list)