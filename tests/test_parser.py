"""
Pytest test suite for Lab 4: Parser & AST.

Run with:  pytest tests/ -v
"""
import pytest
from src.lexer import Lexer
from src.parser import Parser, ParseError
from src.ast_nodes import (
    Program, Block,
    IntegerLiteral, FloatLiteral, StringLiteral, BooleanLiteral, Identifier,
    BinaryOp, UnaryOp, Assignment, FunctionCall, BuiltinCall,
    ExpressionStatement, LetStatement, ReturnStatement,
    IfStatement, WhileStatement, FunctionDef,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def parse(source: str) -> Program:
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


def first(source: str):
    """Return the first statement of the parsed program."""
    return parse(source).statements[0]


# ---------------------------------------------------------------------------
# Integer / float literals
# ---------------------------------------------------------------------------

class TestLiterals:
    def test_integer(self):
        node = first("42\n")
        assert isinstance(node, ExpressionStatement)
        assert isinstance(node.expression, IntegerLiteral)
        assert node.expression.value == 42

    def test_float(self):
        node = first("3.14\n")
        assert isinstance(node.expression, FloatLiteral)
        assert node.expression.value == pytest.approx(3.14)

    def test_string(self):
        node = first('"hello"\n')
        assert isinstance(node.expression, StringLiteral)
        assert node.expression.value == "hello"

    def test_boolean_true(self):
        node = first("true\n")
        assert isinstance(node.expression, BooleanLiteral)
        assert node.expression.value is True

    def test_boolean_false(self):
        node = first("false\n")
        assert isinstance(node.expression, BooleanLiteral)
        assert node.expression.value is False


# ---------------------------------------------------------------------------
# Arithmetic precedence and associativity
# ---------------------------------------------------------------------------

class TestArithmetic:
    def test_addition(self):
        expr = first("1 + 2\n").expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "+"

    def test_precedence_mul_before_add(self):
        # 2 + 3 * 4  =>  2 + (3 * 4)
        expr = first("2 + 3 * 4\n").expression
        assert expr.operator == "+"
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == "*"

    def test_precedence_paren_overrides(self):
        # (2 + 3) * 4  =>  (2 + 3) * 4
        expr = first("(2 + 3) * 4\n").expression
        assert expr.operator == "*"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == "+"

    def test_power_right_associative(self):
        # 2 ^ 3 ^ 4  =>  2 ^ (3 ^ 4)
        expr = first("2 ^ 3 ^ 4\n").expression
        assert expr.operator == "^"
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == "^"

    def test_unary_minus(self):
        expr = first("-5\n").expression
        assert isinstance(expr, UnaryOp)
        assert expr.operator == "-"
        assert isinstance(expr.operand, IntegerLiteral)

    def test_modulo(self):
        expr = first("10 % 3\n").expression
        assert expr.operator == "%"


# ---------------------------------------------------------------------------
# Comparison and logical operators
# ---------------------------------------------------------------------------

class TestLogical:
    def test_equality(self):
        expr = first("a == b\n").expression
        assert expr.operator == "=="

    def test_not_equal(self):
        expr = first("a != b\n").expression
        assert expr.operator == "!="

    def test_less_than(self):
        expr = first("x < 0\n").expression
        assert expr.operator == "<"

    def test_logical_and(self):
        expr = first("a and b\n").expression
        assert expr.operator == "and"

    def test_logical_or(self):
        expr = first("a or b\n").expression
        assert expr.operator == "or"

    def test_logical_not(self):
        expr = first("not x\n").expression
        assert isinstance(expr, UnaryOp)
        assert expr.operator == "not"


# ---------------------------------------------------------------------------
# Variable declarations
# ---------------------------------------------------------------------------

class TestLetStatement:
    def test_basic(self):
        node = first("let x = 10\n")
        assert isinstance(node, LetStatement)
        assert node.name == "x"
        assert isinstance(node.initializer, IntegerLiteral)
        assert node.initializer.value == 10

    def test_expression_initializer(self):
        node = first("let y = x * 2 + 1\n")
        assert isinstance(node, LetStatement)
        # top node of expression should be '+'
        assert isinstance(node.initializer, BinaryOp)
        assert node.initializer.operator == "+"

    def test_string_initializer(self):
        node = first('let msg = "hello"\n')
        assert isinstance(node.initializer, StringLiteral)


# ---------------------------------------------------------------------------
# Assignment expression
# ---------------------------------------------------------------------------

class TestAssignment:
    def test_simple_assignment(self):
        node = first("x = 5\n")
        assert isinstance(node, ExpressionStatement)
        assert isinstance(node.expression, Assignment)
        assert node.expression.name == "x"


# ---------------------------------------------------------------------------
# Function definition
# ---------------------------------------------------------------------------

class TestFunctionDef:
    def test_no_params(self):
        node = first("fn greet() {\n    return 1\n}\n")
        assert isinstance(node, FunctionDef)
        assert node.name == "greet"
        assert node.params == []

    def test_with_params(self):
        node = first("fn add(a, b) {\n    return a\n}\n")
        assert isinstance(node, FunctionDef)
        assert node.params == ["a", "b"]

    def test_body_is_block(self):
        node = first("fn f() {\n    let x = 1\n}\n")
        assert isinstance(node.body, Block)
        assert isinstance(node.body.statements[0], LetStatement)


# ---------------------------------------------------------------------------
# If / else
# ---------------------------------------------------------------------------

class TestIfStatement:
    def test_if_only(self):
        src = "if (x > 0) {\n    let y = 1\n}\n"
        node = first(src)
        assert isinstance(node, IfStatement)
        assert node.else_branch is None

    def test_if_else(self):
        src = "if (x > 0) {\n    return x\n} else {\n    return 0\n}\n"
        node = first(src)
        assert isinstance(node, IfStatement)
        assert node.else_branch is not None


# ---------------------------------------------------------------------------
# While loop
# ---------------------------------------------------------------------------

class TestWhileStatement:
    def test_while(self):
        src = "while (i < 10) {\n    i = i + 1\n}\n"
        node = first(src)
        assert isinstance(node, WhileStatement)
        assert isinstance(node.condition, BinaryOp)
        assert node.condition.operator == "<"


# ---------------------------------------------------------------------------
# Function call
# ---------------------------------------------------------------------------

class TestFunctionCall:
    def test_no_args(self):
        node = first("foo()\n").expression
        assert isinstance(node, FunctionCall)
        assert node.name == "foo"
        assert node.arguments == []

    def test_with_args(self):
        node = first("add(1, 2)\n").expression
        assert isinstance(node, FunctionCall)
        assert len(node.arguments) == 2

    def test_nested_call(self):
        node = first("f(g(1))\n").expression
        assert isinstance(node, FunctionCall)
        assert isinstance(node.arguments[0], FunctionCall)


# ---------------------------------------------------------------------------
# Built-in math functions
# ---------------------------------------------------------------------------

class TestBuiltinCall:
    def test_sqrt(self):
        node = first("sqrt(9)\n").expression
        assert isinstance(node, BuiltinCall)
        assert node.function == "sqrt"

    def test_sin(self):
        node = first("sin(x)\n").expression
        assert isinstance(node, BuiltinCall)
        assert node.function == "sin"

    def test_abs(self):
        node = first("abs(-3)\n").expression
        assert isinstance(node, BuiltinCall)


# ---------------------------------------------------------------------------
# Return statement
# ---------------------------------------------------------------------------

class TestReturnStatement:
    def test_return_value(self):
        src = "fn f() {\n    return 42\n}\n"
        fn = first(src)
        ret = fn.body.statements[0]
        assert isinstance(ret, ReturnStatement)
        assert isinstance(ret.value, IntegerLiteral)


# ---------------------------------------------------------------------------
# Multi-statement program
# ---------------------------------------------------------------------------

class TestProgram:
    def test_multiple_statements(self):
        src = "let a = 1\nlet b = 2\nlet c = a + b\n"
        prog = parse(src)
        assert len(prog.statements) == 3
        assert all(isinstance(s, LetStatement) for s in prog.statements)

    def test_empty_program(self):
        prog = parse("")
        assert prog.statements == []


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestParseErrors:
    def test_missing_rparen(self):
        with pytest.raises(ParseError):
            parse("(1 + 2\n")

    def test_missing_rbrace(self):
        with pytest.raises(ParseError):
            parse("fn f() {\n    let x = 1\n")

    def test_unexpected_token(self):
        with pytest.raises(ParseError):
            parse("let = 5\n")