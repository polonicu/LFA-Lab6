"""
Recursive-descent parser for the scripting language.

Takes the flat token list produced by the Lexer and builds an AST
whose root is a Program node.

Operator precedences (low to high):
    assignment   (right-associative)
    or
    and
    equality          ==  !=
    comparison        <  >  <=  >=
    term              +  -
    factor            *  /  %
    power             ^  (right-associative)
    unary             not  -
    call              f(...)
    primary           literals, identifiers, grouping
"""
from __future__ import annotations

from src.token import Token
from src.token_type import TokenType
from src.ast_nodes import (
    ASTNode, Program, Block,
    IntegerLiteral, FloatLiteral, StringLiteral, BooleanLiteral, Identifier,
    BinaryOp, UnaryOp, Assignment, FunctionCall, BuiltinCall,
    ExpressionStatement, LetStatement, ReturnStatement,
    IfStatement, WhileStatement, ForStatement, FunctionDef,
)

_BUILTINS: frozenset[TokenType] = frozenset({
    TokenType.SIN, TokenType.COS, TokenType.TAN, TokenType.SQRT, TokenType.ABS,
})


class ParseError(Exception):
    def __init__(self, message: str, token: Token) -> None:
        super().__init__(f"{message} -- got {token!r}")
        self.token = token


class Parser:
    """
    Recursive-descent parser.

    Usage::

        tokens = Lexer(source).tokenize()
        ast    = Parser(tokens).parse()
    """

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def parse(self) -> Program:
        statements: list[ASTNode] = []
        self._skip_newlines()
        while not self._at_end():
            statements.append(self._statement())
            self._skip_newlines()
        return Program(statements=statements)

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _statement(self) -> ASTNode:
        tok = self._peek()
        if tok.type == TokenType.FN:
            return self._fn_def()
        if tok.type == TokenType.LET:
            return self._let_stmt()
        if tok.type == TokenType.RETURN:
            return self._return_stmt()
        if tok.type == TokenType.IF:
            return self._if_stmt()
        if tok.type == TokenType.WHILE:
            return self._while_stmt()
        if tok.type == TokenType.FOR:
            return self._for_stmt()
        return self._expr_stmt()

    def _fn_def(self) -> FunctionDef:
        self._consume(TokenType.FN)
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.LPAREN)
        params: list[str] = []
        if self._peek().type != TokenType.RPAREN:
            params.append(self._consume(TokenType.IDENTIFIER).value)
            while self._match(TokenType.COMMA):
                params.append(self._consume(TokenType.IDENTIFIER).value)
        self._consume(TokenType.RPAREN)
        # optional return-type annotation:  -> type_name  (just skip it)
        if self._peek().type == TokenType.ARROW:
            self._advance()
            self._advance()  # skip type identifier
        body = self._block()
        return FunctionDef(name=name, params=params, body=body)

    def _let_stmt(self) -> LetStatement:
        self._consume(TokenType.LET)
        name = self._consume(TokenType.IDENTIFIER).value
        self._consume(TokenType.ASSIGN)
        initializer = self._expression()
        self._skip_newlines()
        return LetStatement(name=name, initializer=initializer)

    def _return_stmt(self) -> ReturnStatement:
        self._consume(TokenType.RETURN)
        value = self._expression()
        self._skip_newlines()
        return ReturnStatement(value=value)

    def _if_stmt(self) -> IfStatement:
        self._consume(TokenType.IF)
        self._consume(TokenType.LPAREN)
        condition = self._expression()
        self._consume(TokenType.RPAREN)
        then_branch = self._block()
        else_branch = None
        self._skip_newlines()
        if self._peek().type == TokenType.ELSE:
            self._advance()
            else_branch = self._block()
        return IfStatement(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def _while_stmt(self) -> WhileStatement:
        self._consume(TokenType.WHILE)
        self._consume(TokenType.LPAREN)
        condition = self._expression()
        self._consume(TokenType.RPAREN)
        body = self._block()
        return WhileStatement(condition=condition, body=body)

    def _for_stmt(self) -> ForStatement:
        self._consume(TokenType.FOR)
        self._consume(TokenType.LPAREN)
        init = self._let_stmt()
        # let_stmt already skips newlines; we need a semicolon
        # (accept either ; or newline as separator inside for-header)
        if self._peek().type == TokenType.SEMICOLON:
            self._advance()
        self._skip_newlines()
        condition = self._expression()
        if self._peek().type == TokenType.SEMICOLON:
            self._advance()
        self._skip_newlines()
        update = self._expression()
        self._consume(TokenType.RPAREN)
        body = self._block()
        return ForStatement(init=init, condition=condition, update=update, body=body)

    def _expr_stmt(self) -> ExpressionStatement:
        expr = self._expression()
        self._skip_newlines()
        return ExpressionStatement(expression=expr)

    def _block(self) -> Block:
        self._consume(TokenType.LBRACE)
        self._skip_newlines()
        stmts: list[ASTNode] = []
        while self._peek().type != TokenType.RBRACE and not self._at_end():
            stmts.append(self._statement())
            self._skip_newlines()
        self._consume(TokenType.RBRACE)
        return Block(statements=stmts)

    # ------------------------------------------------------------------
    # Expressions (Pratt-style precedence climbing via recursive descent)
    # ------------------------------------------------------------------

    def _expression(self) -> ASTNode:
        return self._assignment()

    def _assignment(self) -> ASTNode:
        # Look-ahead: if IDENTIFIER followed by ASSIGN it is an assignment
        if (self._peek().type == TokenType.IDENTIFIER
                and self._peek_at(1).type == TokenType.ASSIGN):
            name = self._advance().value
            self._advance()  # consume '='
            value = self._assignment()  # right-associative
            return Assignment(name=name, value=value)
        return self._logical_or()

    def _logical_or(self) -> ASTNode:
        node = self._logical_and()
        while self._peek().type == TokenType.OR:
            op = self._advance().value
            right = self._logical_and()
            node = BinaryOp(operator=op, left=node, right=right)
        return node

    def _logical_and(self) -> ASTNode:
        node = self._equality()
        while self._peek().type == TokenType.AND:
            op = self._advance().value
            right = self._equality()
            node = BinaryOp(operator=op, left=node, right=right)
        return node

    def _equality(self) -> ASTNode:
        node = self._comparison()
        while self._peek().type in (TokenType.EQ, TokenType.NEQ):
            op = self._advance().value
            right = self._comparison()
            node = BinaryOp(operator=op, left=node, right=right)
        return node

    def _comparison(self) -> ASTNode:
        node = self._term()
        while self._peek().type in (TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self._advance().value
            right = self._term()
            node = BinaryOp(operator=op, left=node, right=right)
        return node

    def _term(self) -> ASTNode:
        node = self._factor()
        while self._peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._factor()
            node = BinaryOp(operator=op, left=node, right=right)
        return node

    def _factor(self) -> ASTNode:
        node = self._power()
        while self._peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._advance().value
            right = self._power()
            node = BinaryOp(operator=op, left=node, right=right)
        return node

    def _power(self) -> ASTNode:
        base = self._unary()
        if self._peek().type == TokenType.CARET:
            op = self._advance().value
            exp = self._power()  # right-associative
            return BinaryOp(operator=op, left=base, right=exp)
        return base

    def _unary(self) -> ASTNode:
        if self._peek().type in (TokenType.NOT, TokenType.MINUS):
            op = self._advance().value
            operand = self._unary()
            return UnaryOp(operator=op, operand=operand)
        return self._call()

    def _call(self) -> ASTNode:
        node = self._primary()
        # user-defined function call:  already handled in primary for IDENTIFIER
        # but we also support chained calls if ever needed
        while self._peek().type == TokenType.LPAREN:
            if isinstance(node, Identifier):
                self._advance()  # consume '('
                args = self._argument_list()
                self._consume(TokenType.RPAREN)
                node = FunctionCall(name=node.name, arguments=args)
            else:
                break
        return node

    def _primary(self) -> ASTNode:
        tok = self._peek()

        if tok.type == TokenType.INTEGER:
            self._advance()
            return IntegerLiteral(value=tok.value)

        if tok.type == TokenType.FLOAT:
            self._advance()
            return FloatLiteral(value=tok.value)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringLiteral(value=tok.value)

        if tok.type == TokenType.BOOLEAN:
            self._advance()
            return BooleanLiteral(value=tok.value)

        if tok.type in _BUILTINS:
            func_name = self._advance().value
            self._consume(TokenType.LPAREN)
            arg = self._expression()
            self._consume(TokenType.RPAREN)
            return BuiltinCall(function=func_name, argument=arg)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            if self._peek().type == TokenType.LPAREN:
                self._advance()  # consume '('
                args = self._argument_list()
                self._consume(TokenType.RPAREN)
                return FunctionCall(name=tok.value, arguments=args)
            return Identifier(name=tok.value)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._expression()
            self._consume(TokenType.RPAREN)
            return expr

        raise ParseError(f"Unexpected token in expression", tok)

    def _argument_list(self) -> list[ASTNode]:
        args: list[ASTNode] = []
        if self._peek().type == TokenType.RPAREN:
            return args
        args.append(self._expression())
        while self._match(TokenType.COMMA):
            args.append(self._expression())
        return args

    # ------------------------------------------------------------------
    # Token stream utilities
    # ------------------------------------------------------------------

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _peek_at(self, offset: int) -> Token:
        idx = self._pos + offset
        if idx >= len(self._tokens):
            return self._tokens[-1]  # EOF
        return self._tokens[idx]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _at_end(self) -> bool:
        return self._tokens[self._pos].type == TokenType.EOF

    def _consume(self, expected: TokenType) -> Token:
        tok = self._peek()
        if tok.type != expected:
            raise ParseError(f"Expected {expected.name}", tok)
        return self._advance()

    def _match(self, *types: TokenType) -> bool:
        if self._peek().type in types:
            self._advance()
            return True
        return False

    def _skip_newlines(self) -> None:
        while self._peek().type == TokenType.NEWLINE:
            self._advance()