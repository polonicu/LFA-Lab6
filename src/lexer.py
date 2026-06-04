"""
Lexer for the scripting language.
Produces a flat list of Token objects from a source string.
"""
from __future__ import annotations

from src.token import Token
from src.token_type import TokenType, TOKEN_PATTERNS, KEYWORD_MAP


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"{message} (line {line}, col {column})")
        self.line = line
        self.column = column


class Lexer:
    """
    Single-pass lexer that walks the source string left to right, attempting
    to match each TOKEN_PATTERNS entry at the current position.  Whitespace
    (excluding newlines) is skipped silently.  Comments are consumed but not
    emitted.  Newlines are emitted as explicit NEWLINE tokens.
    """

    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = 0
        self._line = 1
        self._col = 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self._pos < len(self._source):
            token = self._next_token()
            if token is None:
                continue
            if token.type in (TokenType.COMMENT,):
                continue
            tokens.append(token)
        tokens.append(Token(TokenType.EOF, None, self._line, self._col))
        return tokens

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_token(self) -> Token | None:
        # Skip spaces and tabs
        if self._source[self._pos] in (" ", "\t", "\r"):
            self._pos += 1
            self._col += 1
            return None

        start_line = self._line
        start_col = self._col

        for token_type, pattern in TOKEN_PATTERNS:
            match = pattern.match(self._source, self._pos)
            if match is None:
                continue

            lexeme = match.group(0)
            self._advance(len(lexeme))

            # Resolve identifiers to keywords / booleans
            if token_type == TokenType.IDENTIFIER:
                kw = KEYWORD_MAP.get(lexeme)
                if kw is not None:
                    token_type = kw

            value = self._coerce(token_type, lexeme)
            return Token(token_type, value, start_line, start_col)

        # Nothing matched
        bad_char = self._source[self._pos]
        self._advance(1)
        return Token(TokenType.UNKNOWN, bad_char, start_line, start_col)

    def _advance(self, n: int) -> None:
        for _ in range(n):
            if self._pos < len(self._source) and self._source[self._pos] == "\n":
                self._line += 1
                self._col = 1
            else:
                self._col += 1
            self._pos += 1

    @staticmethod
    def _coerce(token_type: TokenType, lexeme: str) -> object:
        if token_type == TokenType.INTEGER:
            return int(lexeme)
        if token_type == TokenType.FLOAT:
            return float(lexeme)
        if token_type == TokenType.BOOLEAN:
            return lexeme == "true"
        if token_type == TokenType.STRING:
            return lexeme[1:-1].encode("raw_unicode_escape").decode("unicode_escape")
        return lexeme