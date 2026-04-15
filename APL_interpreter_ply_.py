"""
Mark Vernon: Code Execution Developer
Implements the runtime interpreter for the NovaLang (APL) language.
"""

from APL_semantic_ply_ import (
    ASTNode, ProgramNode, AssignNode, DisplayNode, TryCatchNode,
    IfNode, WhileNode, ForNode, FuncDefNode, ReturnNode, FuncCallNode,
    BinOpNode, LiteralNode, IdentifierNode, compile_novalang
)

class ReturnValue(Exception):
    """Custom exception to handle the 'return' statement across call stacks."""
    def __init__(self, value):
        self.value = value

class Environment:
    """Manages variable storage for a specific scope."""
    def __init__(self, parent=None):
        self.variables = {}
        self.parent = parent

    def set(self, name, value):
        self.variables[name] = value

    def get(self, name):
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Variable '{name}' is not defined.")

    def assign(self, name, value):
        """Update an existing variable in the closest scope it was defined."""
        if name in self.variables:
            self.variables[name] = value
        elif self.parent:
            self.parent.assign(name, value)
        else:
            raise NameError(f"Variable '{name}' is not defined.")

class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.functions = {}
        self.output = []

    def log(self, *args):
        message = " ".join(map(str, args))
        self.output.append(message)
        print(message)

    def interpret(self, node, env=None):
        if node is None:
            return None
        if env is None:
            env = self.global_env
        
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, env)

    def generic_visit(self, node, env):
        raise Exception(f'No visit_{type(node).__name__} method')

    def visit_ProgramNode(self, node, env):
        for statement in node.statements:
            self.interpret(statement, env)

    def visit_AssignNode(self, node, env):
        value = self.interpret(node.expr, env)
        # If it's a 'let' (declared_type is not None in some cases or just a new var)
        # The semantic analyzer already checked if it should be declared.
        # For simplicity, we'll see if it exists in the current scope or parents.
        try:
            env.assign(node.name, value)
        except NameError:
            env.set(node.name, value)
        return value

    def visit_DisplayNode(self, node, env):
        values = [self.interpret(arg, env) for arg in node.args]
        self.log(*values)

    def visit_BinOpNode(self, node, env):
        left = self.interpret(node.left, env)
        right = self.interpret(node.right, env)

        if node.op == '+': return left + right
        if node.op == '-': return left - right
        if node.op == '*': return left * right
        if node.op == '/':
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
        if node.op == '==': return left == right
        if node.op == '<': return left < right
        if node.op == '>': return left > right
        if node.op == 'and': return left and right
        if node.op == 'or': return left or right
        return None

    def visit_LiteralNode(self, node, env):
        return node.value

    def visit_IdentifierNode(self, node, env):
        return env.get(node.name)

    def visit_IfNode(self, node, env):
        condition = self.interpret(node.condition, env)
        if condition:
            for stmt in node.then_body:
                self.interpret(stmt, env)
        elif node.else_body:
            for stmt in node.else_body:
                self.interpret(stmt, env)

    def visit_WhileNode(self, node, env):
        while self.interpret(node.condition, env):
            for stmt in node.body:
                self.interpret(stmt, env)

    def visit_ForNode(self, node, env):
        start = self.interpret(node.start, env)
        end = self.interpret(node.end, env)
        loop_env = Environment(env)
        for i in range(int(start), int(end)):
            loop_env.set(node.var, i)
            for stmt in node.body:
                self.interpret(stmt, loop_env)

    def visit_FuncDefNode(self, node, env):
        self.functions[node.name] = node

    def visit_FuncCallNode(self, node, env):
        func_def = self.functions.get(node.name)
        if not func_def:
            raise NameError(f"Function '{node.name}' not defined.")
        
        # Evaluate arguments
        args = [self.interpret(arg, env) for arg in node.args]
        
        # Create function scope
        func_env = Environment(self.global_env) # Functions use global scope + params
        for (param_type, param_name), arg_val in zip(func_def.params, args):
            func_env.set(param_name, arg_val)
        
        try:
            for stmt in func_def.body:
                self.interpret(stmt, func_env)
        except ReturnValue as rv:
            return rv.value
        return None

    def visit_ReturnNode(self, node, env):
        value = self.interpret(node.expr, env)
        raise ReturnValue(value)

    def visit_TryCatchNode(self, node, env):
        try:
            try_env = Environment(env)
            for stmt in node.try_body:
                self.interpret(stmt, try_env)
        except Exception as e:
            catch_env = Environment(env)
            # You could bind the error to a variable here if the language supported it
            for stmt in node.catch_body:
                self.interpret(stmt, catch_env)

def run_interpreter(source: str, show_phases: bool = False):
    """
    1. Parse and Semantic Check
    2. Execute AST (if valid)
    """
    ast, analyzer = compile_novalang(
        source, 
        print_tokens=show_phases, 
        print_ast=show_phases, 
        print_report=show_phases
    )
    if ast is None:
        return "[SYSTEM] Syntax Error: Execution aborted because the code could not be geometrically parsed.", []
        
    if analyzer.errors:
        return "\n".join(analyzer.errors), []

    # 2. Execute
    interpreter = Interpreter()
    try:
        interpreter.interpret(ast)
        return None, interpreter.output
    except Exception as e:
        return f"Runtime Error: {str(e)}", interpreter.output

if __name__ == "__main__":
    code = """
    let int A = 10
    let int B = 20
    display "Sum of A and B is:" (A + B)

    func multiply(int X int Y)
        return X * Y
    end

    display "Product of 5 and 6 is:" multiply(5 6)

    try
        let int C = 10 / 0
    catch
        display "Caught division by zero!"
    end
    """
    err, out = run_interpreter(code)
    if err:
        print(f"Error: {err}")
    else:
        print("Output:")
        for line in out:
            print(line)
