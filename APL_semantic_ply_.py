""" Semantic Analysis Developer
Implements AST construction and semantic analysis for the NovaLang compiler.

This module:
  1. Re-defines parser grammar rules WITH AST node construction
     (the original parser used `pass` — producing no tree).
  2. Defines all AST node classes.
  3. Implements a SemanticAnalyzer that walks the AST and checks:
       • Undeclared variable use
       • Duplicate variable declarations in the same scope
       • Type mismatches in assignments and binary operations
       • Division by zero (literal)
       • Return outside a function
       • Undeclared function calls
       • Argument count mismatch on function calls
  4. Provides a symbol table with nested scope support.
"""

import ply.yacc as yacc
from APL_lexer_ply_ import tokens, lexer   # re-use the PLY lexer


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – AST NODE CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class ASTNode:
    """Base class for every node in the Abstract Syntax Tree."""
    pass


class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements          # list[ASTNode]

    def __repr__(self):
        return f"Program({len(self.statements)} stmts)"


class AssignNode(ASTNode):
    """let [type] IDENTIFIER = expression   OR   IDENTIFIER = expression"""
    def __init__(self, name, expr, declared_type=None, line=None):
        self.name          = name            # str
        self.expr          = expr            # ASTNode
        self.declared_type = declared_type   # 'int'|'float'|'string'|'char'|'bool'|None
        self.line          = line            # int

    def __repr__(self):
        t = f":{self.declared_type}" if self.declared_type else ""
        return f"Assign({self.name}{t} = {self.expr})"


class DisplayNode(ASTNode):
    def __init__(self, args, line=None):
        self.args = args    # list[ASTNode]
        self.line = line

    def __repr__(self):
        return f"Display({self.args})"


class TryCatchNode(ASTNode):
    def __init__(self, try_body, catch_body, line=None):
        self.try_body   = try_body    # list[ASTNode]
        self.catch_body = catch_body  # list[ASTNode]
        self.line       = line

    def __repr__(self):
        return "TryCatch(...)"


class IfNode(ASTNode):
    def __init__(self, condition, then_body, else_body=None, line=None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
        self.line      = line

    def __repr__(self):
        return f"If({self.condition})"


class WhileNode(ASTNode):
    def __init__(self, condition, body, line=None):
        self.condition = condition
        self.body      = body
        self.line      = line

    def __repr__(self):
        return f"While({self.condition})"


class ForNode(ASTNode):
    def __init__(self, var, start, end, body, line=None):
        self.var   = var
        self.start = start
        self.end   = end
        self.body  = body
        self.line  = line

    def __repr__(self):
        return f"For({self.var})"


class FuncDefNode(ASTNode):
    def __init__(self, name, params, body, line=None):
        self.name   = name    # str
        self.params = params  # list[(type_str, name_str)]
        self.body   = body    # list[ASTNode]
        self.line   = line

    def __repr__(self):
        return f"FuncDef({self.name}, params={self.params})"


class ReturnNode(ASTNode):
    def __init__(self, expr, line=None):
        self.expr = expr
        self.line = line

    def __repr__(self):
        return f"Return({self.expr})"


class FuncCallNode(ASTNode):
    def __init__(self, name, args, line=None):
        self.name = name
        self.args = args   # list[ASTNode]
        self.line = line

    def __repr__(self):
        return f"Call({self.name}, args={self.args})"


class BinOpNode(ASTNode):
    def __init__(self, op, left, right, line=None):
        self.op    = op
        self.left  = left
        self.right = right
        self.line  = line

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class LiteralNode(ASTNode):
    def __init__(self, value, vtype, line=None):
        self.value = value
        self.vtype = vtype   # 'int'|'float'|'string'|'char'|'bool'
        self.line  = line

    def __repr__(self):
        return f"Lit({self.value!r}:{self.vtype})"


class IdentifierNode(ASTNode):
    def __init__(self, name, line=None):
        self.name = name
        self.line = line

    def __repr__(self):
        return f"Id({self.name})"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – UPDATED PARSER (same grammar, now builds AST nodes)
# ═══════════════════════════════════════════════════════════════════════════════

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQUAL_EQUAL', 'LESS', 'GREATER'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'SLASH'),
)

# ── Program ──────────────────────────────────────────────────────────────────

def p_program(p):
    'program : statement_list'
    p[0] = ProgramNode([s for s in p[1] if s is not None])

# ── Statement list ────────────────────────────────────────────────────────────

def p_statement_list_recursive(p):
    'statement_list : statement_list statement'
    p[0] = p[1] + [p[2]]

def p_statement_list_single(p):
    'statement_list : statement'
    p[0] = [p[1]]

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
    p[0] = p[1]

# ── Assignment ────────────────────────────────────────────────────────────────

def p_assignment_let_typed(p):
    'assignment : LET type IDENTIFIER EQUAL expression'
    p[0] = AssignNode(name=p[3], expr=p[5], declared_type=p[2],
                      line=p.lineno(3))

def p_assignment_let_untyped(p):
    'assignment : LET IDENTIFIER EQUAL expression'
    p[0] = AssignNode(name=p[2], expr=p[4], declared_type=None,
                      line=p.lineno(2))

def p_assignment_reassign(p):
    'assignment : IDENTIFIER EQUAL expression'
    p[0] = AssignNode(name=p[1], expr=p[3], declared_type=None,
                      line=p.lineno(1))

# ── Type keyword ──────────────────────────────────────────────────────────────

def p_type(p):
    '''type : INT
            | FLOAT_T
            | STRING_T
            | CHAR_T
            | BOOL_T'''
    # normalise keyword token → lowercase type string
    # p.slice[1].type gives the TOKEN NAME (e.g. 'INT')
    # p[1] gives the lexeme value (e.g. 'int') — not reliable here
    mapping = {'INT': 'int', 'FLOAT_T': 'float', 'STRING_T': 'string',
               'CHAR_T': 'char', 'BOOL_T': 'bool'}
    token_name = p.slice[1].type   # e.g. 'INT', 'FLOAT_T', etc.
    p[0] = mapping.get(token_name, p[1])  # fallback to p[1] if not found

# ── Display ───────────────────────────────────────────────────────────────────

def p_display_statement(p):
    'display_statement : DISPLAY display_args'
    p[0] = DisplayNode(args=p[2], line=p.lineno(1))

def p_display_args_single(p):
    'display_args : expression'
    p[0] = [p[1]]

def p_display_args_multiple(p):
    'display_args : display_args COMMA expression'
    p[0] = p[1] + [p[3]]

# ── If ────────────────────────────────────────────────────────────────────────

def p_if_no_else(p):
    'if_statement : IF expression statement_list END'
    p[0] = IfNode(condition=p[2], then_body=p[3], else_body=None,
                  line=p.lineno(1))

def p_if_else(p):
    'if_statement : IF expression statement_list ELSE statement_list END'
    p[0] = IfNode(condition=p[2], then_body=p[3], else_body=p[5],
                  line=p.lineno(1))

# ── While ─────────────────────────────────────────────────────────────────────

def p_while_statement(p):
    'while_statement : WHILE expression statement_list END'
    p[0] = WhileNode(condition=p[2], body=p[3], line=p.lineno(1))

# ── For ───────────────────────────────────────────────────────────────────────

def p_for_statement(p):
    'for_statement : FOR IDENTIFIER EQUAL expression expression statement_list END'
    p[0] = ForNode(var=p[2], start=p[4], end=p[5], body=p[6],
                   line=p.lineno(1))

# ── Try-Catch ─────────────────────────────────────────────────────────────────

def p_try_catch_statement(p):
    'try_catch_statement : TRY statement_list CATCH statement_list END'
    p[0] = TryCatchNode(try_body=p[2], catch_body=p[4], line=p.lineno(1))

# ── Function definition ───────────────────────────────────────────────────────

def p_function_definition(p):
    'function_definition : FUNC IDENTIFIER LPAREN parameter_list RPAREN statement_list END'
    p[0] = FuncDefNode(name=p[2], params=p[4], body=p[6], line=p.lineno(2))

# ── Parameters ────────────────────────────────────────────────────────────────

def p_parameter_list_recursive(p):
    'parameter_list : parameter_list COMMA parameter'
    p[0] = p[1] + [p[3]]

def p_parameter_list_single(p):
    'parameter_list : parameter'
    p[0] = [p[1]]

def p_parameter_list_empty(p):
    'parameter_list :'
    p[0] = []

def p_parameter(p):
    'parameter : type IDENTIFIER'
    p[0] = (p[1], p[2])   # (type_str, name_str)

# ── Function call ─────────────────────────────────────────────────────────────

def p_function_call(p):
    'function_call : IDENTIFIER LPAREN argument_list RPAREN'
    p[0] = FuncCallNode(name=p[1], args=p[3], line=p.lineno(1))

# ── Arguments ─────────────────────────────────────────────────────────────────

def p_argument_list_recursive(p):
    'argument_list : argument_list COMMA expression'
    p[0] = p[1] + [p[3]]

def p_argument_list_single(p):
    'argument_list : expression'
    p[0] = [p[1]]

def p_argument_list_empty(p):
    'argument_list :'
    p[0] = []

# ── Return ────────────────────────────────────────────────────────────────────

def p_return_statement(p):
    'return_statement : RETURN expression'
    p[0] = ReturnNode(expr=p[2], line=p.lineno(1))

# ── Expressions ───────────────────────────────────────────────────────────────

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
    p[0] = BinOpNode(op=p[2], left=p[1], right=p[3], line=p.lineno(2))

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_integer(p):
    'expression : INTEGER'
    p[0] = LiteralNode(value=p[1], vtype='int',    line=p.lineno(1))

def p_expression_float(p):
    'expression : FLOAT'
    p[0] = LiteralNode(value=p[1], vtype='float',  line=p.lineno(1))

def p_expression_string(p):
    'expression : STRING'
    p[0] = LiteralNode(value=p[1], vtype='string', line=p.lineno(1))

def p_expression_char(p):
    'expression : CHAR'
    p[0] = LiteralNode(value=p[1], vtype='char',   line=p.lineno(1))

def p_expression_true(p):
    'expression : TRUE'
    p[0] = LiteralNode(value=True,  vtype='bool',  line=p.lineno(1))

def p_expression_false(p):
    'expression : FALSE'
    p[0] = LiteralNode(value=False, vtype='bool',  line=p.lineno(1))

def p_expression_identifier(p):
    'expression : IDENTIFIER'
    p[0] = IdentifierNode(name=p[1], line=p.lineno(1))

def p_expression_function_call(p):
    'expression : function_call'
    p[0] = p[1]

# ── Newline (ignored structurally) ────────────────────────────────────────────

def p_statement_newline(p):
    'statement : NEWLINE'
    p[0] = None

# ── Syntax error ─────────────────────────────────────────────────────────────

def p_error(p):
    if p:
        print(f"[SYNTAX ERROR] Unexpected token '{p.type}' ({p.value!r}) "
              f"at line {p.lineno}")
    else:
        print("[SYNTAX ERROR] Unexpected end of input")


# Build the parser (write tables to a separate file so they don't clash)
parser = yacc.yacc(outputdir='.', tabmodule='sem_parsetab', debug=False)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – SYMBOL TABLE
# ═══════════════════════════════════════════════════════════════════════════════

class Symbol:
    """One entry in the symbol table."""
    def __init__(self, name, kind, dtype=None, params=None, line=None):
        self.name   = name    # str
        self.kind   = kind    # 'variable' | 'function' | 'parameter'
        self.dtype  = dtype   # inferred or declared type string
        self.params = params  # list[(type, name)] for functions
        self.line   = line

    def __repr__(self):
        if self.kind == 'function':
            return f"Symbol(func {self.name}, params={self.params})"
        return f"Symbol({self.kind} {self.name}:{self.dtype})"


class SymbolTable:
    """
    Scoped symbol table implemented as a stack of dicts.
    The outermost scope is index 0; each nested block pushes a new dict.
    """

    def __init__(self):
        self._scopes: list[dict] = [{}]   # start with global scope

    # ── Scope management ──────────────────────────────────────────────────────

    def push_scope(self):
        """Enter a new (nested) scope."""
        self._scopes.append({})

    def pop_scope(self) -> dict:
        """Exit the current scope and return its contents (for debugging)."""
        if len(self._scopes) == 1:
            raise RuntimeError("Cannot pop the global scope.")
        return self._scopes.pop()

    @property
    def depth(self) -> int:
        return len(self._scopes)

    # ── Symbol operations ─────────────────────────────────────────────────────

    def declare(self, symbol: Symbol) -> bool:
        """
        Add a symbol to the CURRENT scope.
        Returns False (and does NOT overwrite) if the name already exists
        in this scope — the caller should raise a duplicate-declaration error.
        """
        current = self._scopes[-1]
        if symbol.name in current:
            return False          # duplicate in this scope
        current[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Symbol | None:
        """
        Search from innermost to outermost scope.
        Returns the Symbol or None if not found anywhere.
        """
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def dump(self) -> str:
        """Return a human-readable representation of all scopes."""
        lines = []
        for depth, scope in enumerate(self._scopes):
            lines.append(f"  Scope[{depth}] (global)" if depth == 0
                         else f"  Scope[{depth}]")
            if not scope:
                lines.append("    (empty)")
            for sym in scope.values():
                lines.append(f"    {sym}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 – SEMANTIC ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

# Type compatibility helpers
NUMERIC_TYPES = {'int', 'float'}

def _infer_literal_type(node: LiteralNode) -> str:
    return node.vtype

def _numeric_result(t1: str, t2: str) -> str:
    """int op int → int; anything involving float → float."""
    if t1 == 'float' or t2 == 'float':
        return 'float'
    return 'int'

def _types_compatible(t1: str | None, t2: str | None) -> bool:
    """Allow int↔float mixing; exact match otherwise."""
    if t1 is None or t2 is None:
        return True   # unknown — allow and check at runtime
    if t1 == t2:
        return True
    if {t1, t2} <= NUMERIC_TYPES:
        return True
    return False


class SemanticError(Exception):
    def __init__(self, message, line=None):
        loc = f" (line {line})" if line else ""
        super().__init__(f"[SEMANTIC ERROR]{loc} {message}")
        self.line = line


class SemanticAnalyzer:
    """
    Walks the AST produced by the parser and performs:
      1. Scope + symbol table construction
      2. Undeclared variable / function detection
      3. Duplicate declaration detection
      4. Type-mismatch detection (assignment & arithmetic)
      5. Literal division-by-zero detection
      6. Return-outside-function detection
      7. Argument count mismatch on function calls
    """

    def __init__(self):
        self.symbols        = SymbolTable()
        self.errors:  list[str] = []
        self.warnings:list[str] = []
        self._in_function   = False   # track whether we're inside a func body
        self._func_name     = None    # for better error messages

    # ── Public entry point ────────────────────────────────────────────────────

    def analyze(self, tree: ProgramNode) -> bool:
        """
        Run full semantic analysis on the AST.
        Returns True if no errors were found, False otherwise.
        Errors and warnings are stored in self.errors / self.warnings.
        """
        self._visit(tree)
        return len(self.errors) == 0

    # ── Internal dispatch ─────────────────────────────────────────────────────

    def _visit(self, node: ASTNode) -> str | None:
        """
        Dispatch to the appropriate _visit_* method.
        Returns the inferred type of the node (for expressions), or None.
        """
        if node is None:
            return None
        method_name = f"_visit_{type(node).__name__}"
        method = getattr(self, method_name, self._visit_unknown)
        return method(node)

    def _visit_unknown(self, node):
        self.warnings.append(f"Unhandled AST node type: {type(node).__name__}")
        return None

    # ── Node visitors ─────────────────────────────────────────────────────────

    def _visit_ProgramNode(self, node: ProgramNode):
        for stmt in node.statements:
            self._visit(stmt)

    def _visit_AssignNode(self, node: AssignNode):
        expr_type = self._visit(node.expr)

        sym = self.symbols.lookup(node.name)

        if sym is None:
            # ── NEW declaration (LET or first assignment)
            declared = node.declared_type or expr_type or 'unknown'
            new_sym = Symbol(name=node.name, kind='variable',
                             dtype=declared, line=node.line)
            if not self.symbols.declare(new_sym):
                self.errors.append(
                    f"[SEMANTIC ERROR] (line {node.line}) "
                    f"Variable '{node.name}' already declared in this scope.")
        else:
            # ── RE-ASSIGNMENT to existing variable
            if node.declared_type is not None and node.declared_type != sym.dtype:
                self.errors.append(
                    f"[SEMANTIC ERROR] (line {node.line}) "
                    f"Cannot re-declare '{node.name}' with a different type "
                    f"(was '{sym.dtype}', got '{node.declared_type}').")
            # Type-check the value being assigned
            if not _types_compatible(sym.dtype, expr_type):
                self.errors.append(
                    f"[SEMANTIC ERROR] (line {node.line}) "
                    f"Type mismatch: cannot assign '{expr_type}' to "
                    f"'{node.name}' which is of type '{sym.dtype}'.")

    def _visit_DisplayNode(self, node: DisplayNode):
        for arg in node.args:
            self._visit(arg)   # ensure identifiers exist etc.

    def _visit_TryCatchNode(self, node: TryCatchNode):
        self.symbols.push_scope()
        for stmt in node.try_body:
            self._visit(stmt)
        self.symbols.pop_scope()

        self.symbols.push_scope()
        for stmt in node.catch_body:
            self._visit(stmt)
        self.symbols.pop_scope()

    def _visit_IfNode(self, node: IfNode):
        cond_type = self._visit(node.condition)
        if cond_type not in (None, 'bool', 'int'):
            self.warnings.append(
                f"[WARNING] (line {node.line}) "
                f"Condition expression has type '{cond_type}'; "
                f"expected bool or int.")

        self.symbols.push_scope()
        for stmt in node.then_body:
            self._visit(stmt)
        self.symbols.pop_scope()

        if node.else_body:
            self.symbols.push_scope()
            for stmt in node.else_body:
                self._visit(stmt)
            self.symbols.pop_scope()

    def _visit_WhileNode(self, node: WhileNode):
        self._visit(node.condition)
        self.symbols.push_scope()
        for stmt in node.body:
            self._visit(stmt)
        self.symbols.pop_scope()

    def _visit_ForNode(self, node: ForNode):
        self._visit(node.start)
        self._visit(node.end)
        self.symbols.push_scope()
        # Declare loop variable inside the loop scope
        loop_sym = Symbol(name=node.var, kind='variable', dtype='int',
                          line=node.line)
        self.symbols.declare(loop_sym)
        for stmt in node.body:
            self._visit(stmt)
        self.symbols.pop_scope()

    def _visit_FuncDefNode(self, node: FuncDefNode):
        # Register the function in the CURRENT (outer) scope first
        func_sym = Symbol(name=node.name, kind='function',
                          dtype='function', params=node.params, line=node.line)
        if not self.symbols.declare(func_sym):
            self.errors.append(
                f"[SEMANTIC ERROR] (line {node.line}) "
                f"Function '{node.name}' already declared.")

        # Analyse the body in a new scope
        prev_in_func = self._in_function
        prev_func_name = self._func_name
        self._in_function = True
        self._func_name   = node.name

        self.symbols.push_scope()
        # Declare parameters inside the function scope
        for (ptype, pname) in node.params:
            param_sym = Symbol(name=pname, kind='parameter',
                               dtype=ptype, line=node.line)
            if not self.symbols.declare(param_sym):
                self.errors.append(
                    f"[SEMANTIC ERROR] (line {node.line}) "
                    f"Duplicate parameter '{pname}' in function '{node.name}'.")
        for stmt in node.body:
            self._visit(stmt)
        self.symbols.pop_scope()

        self._in_function = prev_in_func
        self._func_name   = prev_func_name

    def _visit_ReturnNode(self, node: ReturnNode):
        if not self._in_function:
            self.errors.append(
                f"[SEMANTIC ERROR] (line {node.line}) "
                f"'return' statement used outside of a function.")
        self._visit(node.expr)

    def _visit_FuncCallNode(self, node: FuncCallNode) -> str | None:
        sym = self.symbols.lookup(node.name)
        if sym is None:
            self.errors.append(
                f"[SEMANTIC ERROR] (line {node.line}) "
                f"Call to undeclared function '{node.name}'.")
            return None
        if sym.kind != 'function':
            self.errors.append(
                f"[SEMANTIC ERROR] (line {node.line}) "
                f"'{node.name}' is a variable, not a function.")
            return None
        # Argument count check
        expected = len(sym.params) if sym.params else 0
        actual   = len(node.args)
        if expected != actual:
            self.errors.append(
                f"[SEMANTIC ERROR] (line {node.line}) "
                f"Function '{node.name}' expects {expected} argument(s) "
                f"but received {actual}.")
        for arg in node.args:
            self._visit(arg)
        return None   # return type inference is beyond this scope

    def _visit_BinOpNode(self, node: BinOpNode) -> str | None:
        lt = self._visit(node.left)
        rt = self._visit(node.right)

        # Literal division-by-zero check
        if node.op == '/' and isinstance(node.right, LiteralNode):
            if node.right.value == 0:
                self.errors.append(
                    f"[SEMANTIC ERROR] (line {node.line}) "
                    f"Division by zero detected.")

        comparison_ops = {'==', '<', '>'}
        logical_ops    = {'and', 'or'}

        if node.op in comparison_ops or node.op in logical_ops:
            return 'bool'

        # Arithmetic type resolution
        if node.op in {'+', '-', '*', '/'}:
            if lt in NUMERIC_TYPES and rt in NUMERIC_TYPES:
                return _numeric_result(lt, rt)
            # String concatenation allowed with +
            if node.op == '+' and lt == 'string' and rt == 'string':
                return 'string'
            if lt is not None and rt is not None:
                self.errors.append(
                    f"[SEMANTIC ERROR] (line {node.line}) "
                    f"Type mismatch: operator '{node.op}' applied to "
                    f"'{lt}' and '{rt}'.")
        return lt  # best-effort fallback

    def _visit_LiteralNode(self, node: LiteralNode) -> str:
        return node.vtype

    def _visit_IdentifierNode(self, node: IdentifierNode) -> str | None:
        sym = self.symbols.lookup(node.name)
        if sym is None:
            self.errors.append(
                f"[SEMANTIC ERROR] (line {node.line}) "
                f"Use of undeclared variable '{node.name}'.")
            return None
        return sym.dtype

    # ── Report generation ─────────────────────────────────────────────────────

    def report(self) -> str:
        lines = []
        lines.append("╔══════════════════════════════════════════════════╗")
        lines.append("║         NovaLang Semantic Analysis Report        ║")
        lines.append("╚══════════════════════════════════════════════════╝")

        lines.append("\n── Symbol Table ─────────────────────────────────")
        lines.append(self.symbols.dump())

        if self.errors:
            lines.append(f"\n── Errors ({len(self.errors)}) ──────────────────────────")
            for e in self.errors:
                lines.append(f"  ✗  {e}")
        else:
            lines.append("\n── Errors ───────────────────────────────────────")
            lines.append("  ✔  No semantic errors found.")

        if self.warnings:
            lines.append(f"\n── Warnings ({len(self.warnings)}) ────────────────────────")
            for w in self.warnings:
                lines.append(f"  ⚠  {w}")

        status = "PASSED ✔" if not self.errors else "FAILED ✗"
        lines.append(f"\n── Result ───────────────────────────────────────")
        lines.append(f"  Semantic analysis {status}")
        lines.append("─" * 52)
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 – AST PRETTY PRINTER
# ═══════════════════════════════════════════════════════════════════════════════

class ASTPrinter:
    """Recursively prints the AST in a tree format."""

    def print(self, node: ASTNode, indent: int = 0, prefix: str = "") -> None:
        pad   = "    " * indent
        label = self._label(node)
        print(f"{pad}{prefix}{label}")
        for child_label, child in self._children(node):
            self.print(child, indent + 1, prefix=f"{child_label}: ")

    def _label(self, node) -> str:
        if isinstance(node, ProgramNode):
            return f"Program [{len(node.statements)} statements]"
        if isinstance(node, AssignNode):
            t = f":{node.declared_type}" if node.declared_type else ""
            return f"Assign  '{node.name}'{t}  (line {node.line})"
        if isinstance(node, DisplayNode):
            return f"Display  [{len(node.args)} arg(s)]  (line {node.line})"
        if isinstance(node, TryCatchNode):
            return "TryCatch"
        if isinstance(node, IfNode):
            return f"If  (line {node.line})"
        if isinstance(node, WhileNode):
            return f"While  (line {node.line})"
        if isinstance(node, ForNode):
            return f"For  '{node.var}'  (line {node.line})"
        if isinstance(node, FuncDefNode):
            params = ", ".join(f"{t} {n}" for t, n in node.params)
            return f"FuncDef  '{node.name}({params})'  (line {node.line})"
        if isinstance(node, ReturnNode):
            return f"Return  (line {node.line})"
        if isinstance(node, FuncCallNode):
            return f"Call  '{node.name}'  (line {node.line})"
        if isinstance(node, BinOpNode):
            return f"BinOp  '{node.op}'"
        if isinstance(node, LiteralNode):
            return f"Literal  {node.value!r}  :{node.vtype}"
        if isinstance(node, IdentifierNode):
            return f"Identifier  '{node.name}'"
        return repr(node)

    def _children(self, node):
        if isinstance(node, ProgramNode):
            return [(f"stmt[{i}]", s) for i, s in enumerate(node.statements)]
        if isinstance(node, AssignNode):
            return [("expr", node.expr)]
        if isinstance(node, DisplayNode):
            return [(f"arg[{i}]", a) for i, a in enumerate(node.args)]
        if isinstance(node, TryCatchNode):
            kids  = [(f"try[{i}]",   s) for i, s in enumerate(node.try_body)]
            kids += [(f"catch[{i}]", s) for i, s in enumerate(node.catch_body)]
            return kids
        if isinstance(node, IfNode):
            kids = [("cond", node.condition)]
            kids += [(f"then[{i}]", s) for i, s in enumerate(node.then_body)]
            if node.else_body:
                kids += [(f"else[{i}]", s) for i, s in enumerate(node.else_body)]
            return kids
        if isinstance(node, WhileNode):
            kids = [("cond", node.condition)]
            kids += [(f"body[{i}]", s) for i, s in enumerate(node.body)]
            return kids
        if isinstance(node, ForNode):
            return [("start", node.start), ("end", node.end)] + \
                   [(f"body[{i}]", s) for i, s in enumerate(node.body)]
        if isinstance(node, FuncDefNode):
            return [(f"body[{i}]", s) for i, s in enumerate(node.body)]
        if isinstance(node, ReturnNode):
            return [("expr", node.expr)]
        if isinstance(node, FuncCallNode):
            return [(f"arg[{i}]", a) for i, a in enumerate(node.args)]
        if isinstance(node, BinOpNode):
            return [("left", node.left), ("right", node.right)]
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 – PUBLIC PIPELINE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def compile_novalang(source: str,
                     print_tokens:  bool = False,
                     print_ast:     bool = True,
                     print_report:  bool = True,
                     interactive_pause: bool = False) -> tuple[ProgramNode | None,
                                                          SemanticAnalyzer]:
    """
    Full front-end pipeline:
      source → tokens → AST → semantic analysis

    Returns (ast_root, analyzer).
    If parsing fails, ast_root is None.
    Check analyzer.errors for semantic errors.
    """
    from APL_lexer_ply_ import tokenize, print_token_stream

    # ── 1. Lex ────────────────────────────────────────────────────────────────
    if print_tokens:
        print("═" * 60)
        print("  PHASE 1 — Lexical Analysis (Token Stream)")
        print("═" * 60)
        toks = tokenize(source)
        print_token_stream(toks)
        print()
        if interactive_pause:
            input("\n[PAUSE] Lexical Analysis complete. Press Enter to proceed to Syntax Analysis (Parser)...")
            print()

    # ── 2. Parse ──────────────────────────────────────────────────────────────
    print("═" * 60)
    print("  PHASE 2 — Syntax Analysis (AST Construction)")
    print("═" * 60)
    lexer.input(source)
    lexer.lineno = 1
    ast = parser.parse(source, lexer=lexer)

    if ast is None:
        print("[PARSER] Could not build AST — check syntax errors above.\n")
        return None, SemanticAnalyzer()

    if print_ast:
        print("\n  Parse Tree / AST:\n")
        ASTPrinter().print(ast)
        print()
        if interactive_pause:
            input("\n[PAUSE] Syntax Analysis complete. Press Enter to proceed to Semantic Analysis...")
            print()

    # ── 3. Semantic analysis ──────────────────────────────────────────────────
    print("═" * 60)
    print("  PHASE 3 — Semantic Analysis")
    print("═" * 60)
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if print_report:
        print(analyzer.report())

    return ast, analyzer


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 – DEMO
# ═══════════════════════════════════════════════════════════════════════════════

# ── Program from the project brief (adapted to NovaLang typed-let syntax) ──
BRIEF_PROGRAM = """\
-- Sample program from the project brief
let A = 20
let B = 40
let C = A + B * B
-- Demonstrating Exception Handling
try
    let D = C / 0
catch
    display "Error: Division by zero attempted but not allowed."
end
display "The result is " C
"""

# ── Extended program demonstrating all language features ──
EXTENDED_PROGRAM = """\
-- NovaLang extended demo
let int A = 20
let int B = 40
let int C = A + B * B

-- Function definition
func add(int X int Y)
    return X + Y
end

display "Sum:" add(5 10)

-- If / else
if A == 20
    display "A is twenty"
else
    display "A is not twenty"
end

-- While loop
let bool flag = true
while flag
    display "looping"
    flag = false
end

-- Try / catch
try
    let int D = C / 0
catch
    display "Error: Division by zero"
end

display "The result is " C
"""

# ── Program with deliberate semantic errors ──
ERROR_PROGRAM = """\
-- This program contains semantic errors for testing
let int X = 10
display Y
let int X = 99
return 5
unknownFunc(1 2)
let int Z = "hello"
"""

if __name__ == "__main__":

    print("\n" + "▓" * 60)
    print("  TEST 1 — Project Brief Sample Program")
    print("▓" * 60)
    compile_novalang(BRIEF_PROGRAM, print_tokens=True)

    print("\n" + "▓" * 60)
    print("  TEST 2 — Extended NovaLang Program")
    print("▓" * 60)
    compile_novalang(EXTENDED_PROGRAM, print_tokens=False)

    print("\n" + "▓" * 60)
    print("  TEST 3 — Semantic Error Detection")
    print("▓" * 60)
    compile_novalang(ERROR_PROGRAM, print_tokens=False)
