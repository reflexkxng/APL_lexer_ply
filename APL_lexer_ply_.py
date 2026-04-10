"""
Mark Vernon: Lexical Analysis Developer
Implements tokenization for the NovaLang compiler using PLY's lex module.
"""

import ply.lex as lex

# ─────────────────────────────────────────────────────────────────────────────
# 1. TOKEN LIST
#    Every token the lexer can produce must be listed here.
#    PLY requires this to be a list named exactly 'tokens'.
# ─────────────────────────────────────────────────────────────────────────────

tokens = (
    # ── Literals ──────────────────────────────────────────────────────────────
    'INTEGER',
    'FLOAT',
    'STRING',
    'CHAR',

    # ── Identifier ────────────────────────────────────────────────────────────
    'IDENTIFIER',

    # ── Arithmetic Operators ──────────────────────────────────────────────────
    'PLUS',
    'MINUS',
    'STAR',
    'SLASH',

    # ── Comparison Operators ──────────────────────────────────────────────────
    'EQUAL_EQUAL',
    'LESS',
    'GREATER',

    # ── Assignment ────────────────────────────────────────────────────────────
    'EQUAL',

    # ── Delimiters ────────────────────────────────────────────────────────────
    'LPAREN',
    'RPAREN',
    'COMMA',

    # ── Control ───────────────────────────────────────────────────────────────
    'NEWLINE',
)


# ─────────────────────────────────────────────────────────────────────────────
# 2. KEYWORD TABLE
#    Keywords are NOT in the tokens tuple above.
#    Instead they are resolved from IDENTIFIER tokens via this dictionary.
#    PLY convention: keyword token names are added dynamically.
# ─────────────────────────────────────────────────────────────────────────────

KEYWORDS = {
    'let'     : 'LET',
    'int'     : 'INT',
    'float'   : 'FLOAT_T',
    'string'  : 'STRING_T',
    'char'    : 'CHAR_T',
    'bool'    : 'BOOL_T',
    'display' : 'DISPLAY',
    'if'      : 'IF',
    'else'    : 'ELSE',
    'while'   : 'WHILE',
    'for'     : 'FOR',
    'func'    : 'FUNC',
    'return'  : 'RETURN',
    'try'     : 'TRY',
    'catch'   : 'CATCH',
    'end'     : 'END',
    'true'    : 'TRUE',
    'false'   : 'FALSE',
    'and'     : 'AND',
    'or'      : 'OR',
}

# Extend the tokens tuple to include all keyword token names
tokens = tokens + tuple(KEYWORDS.values())


# ─────────────────────────────────────────────────────────────────────────────
# 3. SIMPLE TOKEN RULES (single-line regex strings)
#    PLY matches variables named t_TOKENNAME to their regex.
#    IMPORTANT: longer/more specific strings must come before shorter ones.
# ─────────────────────────────────────────────────────────────────────────────

t_EQUAL_EQUAL  = r'=='        # must be before t_EQUAL
t_PLUS         = r'\+'
t_MINUS        = r'-'
t_STAR         = r'\*'
t_SLASH        = r'/'
t_LESS         = r'<'
t_GREATER      = r'>'
t_EQUAL        = r'='
t_LPAREN       = r'\('
t_RPAREN       = r'\)'
t_COMMA        = r','

# ─────────────────────────────────────────────────────────────────────────────
# 4. COMPLEX TOKEN RULES (functions)
#    Function rules let us transform t.value and resolve keywords.
#    PLY uses the function's docstring as the regex pattern.
#    Functions are matched before string rules, and among functions,
#    longer docstrings take priority — so FLOAT must come before INTEGER.
# ─────────────────────────────────────────────────────────────────────────────

def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)   # convert lexeme string → Python float
    return t


def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)     # convert lexeme string → Python int
    return t


def t_STRING(t):
    r'"[^"\n]*"'
    t.value = t.value[1:-1]    # strip surrounding double quotes
    return t


def t_CHAR(t):
    r"'[^'\n]'"
    t.value = t.value[1]       # extract the single character inside ''
    return t


def t_IDENTIFIER(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    # Check if the word is a reserved keyword
    t.type = KEYWORDS.get(t.value, 'IDENTIFIER')

    # Convert boolean literals to Python bool values
    if t.type == 'TRUE':
        t.value = True
    elif t.type == 'FALSE':
        t.value = False

    return t


def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1        # PLY tracks line numbers via lexer.lineno
    return t                   # return so NEWLINE appears in the token stream


def t_COMMENT(t):
    r'--[^\n]*'
    pass                       # discard: return nothing → no token emitted


# Whitespace (spaces, tabs, carriage returns) — ignored silently
t_ignore = ' \t\r'


# ─────────────────────────────────────────────────────────────────────────────
# 5. ERROR HANDLER
#    Called by PLY when no rule matches the current character.
# ─────────────────────────────────────────────────────────────────────────────

def t_error(t):
    print(f"[LEXER ERROR] Illegal character {t.value[0]!r} "
          f"at line {t.lineno}")
    t.lexer.skip(1)            # skip the bad character and continue


# ─────────────────────────────────────────────────────────────────────────────
# 6. BUILD THE LEXER
# ─────────────────────────────────────────────────────────────────────────────

lexer = lex.lex()

# ─────────────────────────────────────────────────────────────────────────────
# 7. PUBLIC HELPER — tokenize()
#    Mimics the same interface as the original hand-built lexer so the
#    parser (Member 3) can switch between implementations transparently.
# ─────────────────────────────────────────────────────────────────────────────

class Token:
    """Lightweight wrapper to match the original Token dataclass interface."""
    def __init__(self, type_, lexeme, value, line):
        self.type   = type_
        self.lexeme = lexeme
        self.value  = value
        self.line   = line

    def __repr__(self):
        return (f"Token(type={self.type:<15} "
                f"lexeme={self.lexeme!r:<18} "
                f"value={str(self.value):<15} "
                f"line={self.line})")


def tokenize(source: str) -> list[Token]:
    """
    Tokenise a NovaLang source string and return a list of Token objects.
    Ends with a single EOF token.
    """
    lexer.input(source)
    lexer.lineno = 1

    result = []
    for tok in lexer:
        result.append(Token(tok.type, tok.value, tok.value, tok.lineno))

    result.append(Token('EOF', '', None, lexer.lineno))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 8. PRETTY-PRINT HELPER
# ─────────────────────────────────────────────────────────────────────────────

def print_token_stream(tokens: list[Token]) -> None:
    header = f"{'#':<5} {'TYPE':<15} {'LEXEME / VALUE':<25} {'LINE':>4}"
    print(header)
    print("─" * len(header))
    for i, tok in enumerate(tokens):
        display = repr(tok.lexeme) if isinstance(tok.lexeme, str) else str(tok.lexeme)
        print(f"{i:<5} {tok.type:<15} {display:<25} {tok.line:>4}")


# ─────────────────────────────────────────────────────────────────────────────
# 9. DEMO
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_PROGRAM = """\
-- NovaLang sample program
let int A = 20
let int B = 40
let int C = A + B * B
display "Value of C:", C

func add(int X, int Y)
    return X + Y
end

display add(5, 10)

try
    let int D = C / 0
catch
    display "Error: Division by zero"
end

if A == 20
    display "A is twenty"
else
    display "A is not twenty"
end

let bool flag = true
while flag
    display "looping"
    flag = false
end
"""

if __name__ == "__main__":
    print("=" * 60)
    print("  NovaLang PLY Lexer — Token Stream")
    print("=" * 60)
    print()

    token_list = tokenize(SAMPLE_PROGRAM)
    print_token_stream(token_list)

    # Summary
    print(f"\nTotal tokens : {len(token_list)} (including EOF)")

    from collections import Counter
    counts = Counter(t.type for t in token_list)
    print("\nToken type breakdown:")
    for ttype, count in sorted(counts.items()):
        print(f"  {ttype:<15} : {count}")
