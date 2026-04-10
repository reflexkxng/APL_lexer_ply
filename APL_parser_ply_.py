"""
Zoe-Marie Shaw: Syntax Analysis Developer
Implements parse tree for the NovaLang compiler using PLY's yacc module.
"""

import ply.yacc as yacc

#Uses tokens from the lexer
from APL_lexer_ply_ import tokens

# ---------------------- PRECEDENCE ----------------------
precedence = (
    ('left', 'OR'),                          # Lowest
    ('left', 'AND'),
    ('left', 'EQUAL_EQUAL', 'LESS', 'GREATER'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'SLASH'),              # Highest
)

# ---------------------- PROGRAM ----------------------

def p_program(p):
    'program : statement_list'
    pass

# ---------------------- STATEMENTS ----------------------

def p_statement_list_recursive(p):
    'statement_list : statement_list statement'
    pass

def p_statement_list_single(p):
    'statement_list : statement'
    pass


def p_statement(p):
    '''statement : assignment
                 | display_statement
                 | try_catch_statement
                 | if_statement
                 | while_statement
                 | for_statement
                 | return_statement
                 | function_definition
                 | function_call'''
    pass


# ---------------------- ASSIGNMENT ----------------------

def p_assignment(p):
    '''assignment : LET type IDENTIFIER EQUAL expression
                  | type IDENTIFIER EQUAL expression
                  | IDENTIFIER EQUAL expression'''
    pass


# ---------------------- TYPE ----------------------

def p_type(p):
    '''type : INT
            | FLOAT_T
            | STRING_T
            | CHAR_T
            | BOOL_T'''
    pass


# ---------------------- DISPLAY ----------------------

def p_display_statement(p):
    'display_statement : DISPLAY display_args'
    pass

def p_display_args_single(p):
    'display_args : expression'
    pass

def p_display_args_multiple(p):
    'display_args : display_args COMMA expression'
    pass


# ---------------------- IF ----------------------

def p_if_statement(p):
    '''if_statement : IF expression statement_list END
                    | IF expression statement_list ELSE statement_list END'''
    pass


# ---------------------- WHILE ----------------------

def p_while_statement(p):
    'while_statement : WHILE expression statement_list END'
    pass


# ---------------------- FOR ----------------------

def p_for_statement(p):
    'for_statement : FOR IDENTIFIER EQUAL expression expression statement_list END'
    pass


# ---------------------- TRY-CATCH ----------------------

def p_try_catch_statement(p):
    'try_catch_statement : TRY statement_list CATCH statement_list END'
    pass


# ---------------------- FUNCTION DEF ----------------------

def p_function_definition(p):
    'function_definition : FUNC IDENTIFIER LPAREN parameter_list RPAREN statement_list END'
    pass


# ---------------------- PARAMETERS ----------------------

def p_parameter_list_recursive(p):
    'parameter_list : parameter_list COMMA parameter'
    pass

def p_parameter_list_single(p):
    'parameter_list : parameter'
    pass

def p_parameter_list_empty(p):
    'parameter_list :'
    pass


def p_parameter(p):
    'parameter : type IDENTIFIER'
    pass


# ---------------------- FUNCTION CALL ----------------------

def p_function_call(p):
    'function_call : IDENTIFIER LPAREN argument_list RPAREN'
    pass


# ---------------------- ARGUMENTS ----------------------

def p_argument_list_recursive(p):
    'argument_list : argument_list COMMA expression'
    pass

def p_argument_list_single(p):
    'argument_list : expression'
    pass

def p_argument_list_empty(p):
    'argument_list :'
    pass


# ---------------------- RETURN ----------------------

def p_return_statement(p):
    'return_statement : RETURN expression'
    pass


# ---------------------- EXPRESSIONS ----------------------

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression STAR expression
                  | expression SLASH expression
                  | expression EQUAL_EQUAL expression
                  | expression LESS expression
                  | expression GREATER expression
                  | expression AND expression
                  | expression OR expression'''
    pass


def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    pass


def p_expression_literal(p):
    '''expression : INTEGER
                  | FLOAT
                  | STRING
                  | CHAR
                  | TRUE
                  | FALSE'''
    pass


def p_expression_identifier(p):
    'expression : IDENTIFIER'
    pass


def p_expression_function_call(p):
    'expression : function_call'
    pass

# ---------------------- NEWLINE ----------------------

def p_statement_newline(p):
    'statement : NEWLINE'
    pass

# ---------------------- ERROR ----------------------

def p_error(p):
    if p:
        print(f"[SYNTAX ERROR] Unexpected token {p.type} at line {p.lineno}")
    else:
        print("[SYNTAX ERROR] Unexpected end of input")


# ---------------------- BUILD PARSER ----------------------

parser = yacc.yacc(method='SLR')

if __name__ == "__main__":
    while True:
        try:
            line = input('NovaLang> ')
        except EOFError:
            break

        if not line: continue

        print("\n--- PARSER OUTPUT ---")
        result = parser.parse(line)
        print(result)