"""
TokenType enum for the scripting language lexer.
Every token category is identified by a regex pattern; the Lexer
iterates through them in priority order.
"""
import re
from enum import Enum, auto


class TokenType(Enum):
    # Literals
    FLOAT      = auto()
    INTEGER    = auto()
    STRING     = auto()
    BOOLEAN    = auto()

    # Identifiers / keywords (resolved after matching IDENTIFIER)
    IF         = auto()
    ELSE       = auto()
    WHILE      = auto()
    FOR        = auto()
    RETURN     = auto()
    LET        = auto()
    FN         = auto()
    AND        = auto()
    OR         = auto()
    NOT        = auto()
    SIN        = auto()
    COS        = auto()
    TAN        = auto()
    SQRT       = auto()
    ABS        = auto()
    IDENTIFIER = auto()

    # Multi-character operators (must come before single-char)
    ARROW      = auto()   # ->
    EQ         = auto()   # ==
    NEQ        = auto()   # !=
    LTE        = auto()   # <=
    GTE        = auto()   # >=

    # Single-character operators
    ASSIGN     = auto()   # =
    LT         = auto()   # <
    GT         = auto()   # >
    PLUS       = auto()
    MINUS      = auto()
    STAR       = auto()
    SLASH      = auto()
    PERCENT    = auto()
    CARET      = auto()

    # Delimiters
    LPAREN     = auto()
    RPAREN     = auto()
    LBRACE     = auto()
    RBRACE     = auto()
    LBRACKET   = auto()
    RBRACKET   = auto()
    COMMA      = auto()
    SEMICOLON  = auto()
    COLON      = auto()
    DOT        = auto()

    # Misc
    COMMENT    = auto()
    NEWLINE    = auto()
    EOF        = auto()
    UNKNOWN    = auto()


# ---------------------------------------------------------------------------
# Regex patterns used by the Lexer (order matters: more specific first)
# ---------------------------------------------------------------------------

KEYWORD_MAP: dict[str, TokenType] = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "return": TokenType.RETURN,
    "let": TokenType.LET,
    "fn": TokenType.FN,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "sin": TokenType.SIN,
    "cos": TokenType.COS,
    "tan": TokenType.TAN,
    "sqrt": TokenType.SQRT,
    "abs": TokenType.ABS,
    "true": TokenType.BOOLEAN,
    "false": TokenType.BOOLEAN,
}

TOKEN_PATTERNS: list[tuple[TokenType, re.Pattern[str]]] = [
    (TokenType.FLOAT,     re.compile(r"\d+\.\d*([eE][+-]?\d+)?|\d+[eE][+-]?\d+")),
    (TokenType.INTEGER,   re.compile(r"\d+")),
    (TokenType.STRING,    re.compile(r'"(?:[^"\\]|\\.)*"')),
    (TokenType.IDENTIFIER, re.compile(r"[a-zA-Z_]\w*")),
    (TokenType.ARROW,     re.compile(r"->")),
    (TokenType.EQ,        re.compile(r"==")),
    (TokenType.NEQ,       re.compile(r"!=")),
    (TokenType.LTE,       re.compile(r"<=")),
    (TokenType.GTE,       re.compile(r">=")),
    (TokenType.ASSIGN,    re.compile(r"=")),
    (TokenType.LT,        re.compile(r"<")),
    (TokenType.GT,        re.compile(r">")),
    (TokenType.PLUS,      re.compile(r"\+")),
    (TokenType.MINUS,     re.compile(r"-")),
    (TokenType.STAR,      re.compile(r"\*")),
    (TokenType.SLASH,     re.compile(r"/")),
    (TokenType.PERCENT,   re.compile(r"%")),
    (TokenType.CARET,     re.compile(r"\^")),
    (TokenType.LPAREN,    re.compile(r"\(")),
    (TokenType.RPAREN,    re.compile(r"\)")),
    (TokenType.LBRACE,    re.compile(r"\{")),
    (TokenType.RBRACE,    re.compile(r"\}")),
    (TokenType.LBRACKET,  re.compile(r"\[")),
    (TokenType.RBRACKET,  re.compile(r"\]")),
    (TokenType.COMMA,     re.compile(r",")),
    (TokenType.SEMICOLON, re.compile(r";")),
    (TokenType.COLON,     re.compile(r":")),
    (TokenType.DOT,       re.compile(r"\.")),
    (TokenType.COMMENT,   re.compile(r"#[^\n]*")),
    (TokenType.NEWLINE,   re.compile(r"\n")),
]