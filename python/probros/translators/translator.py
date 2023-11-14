
# %%
# https://github.com/python/cpython/blob/3.12/Lib/ast.py
from _ast import FunctionDef
import ast
from contextlib import contextmanager, nullcontext
from abc import ABC, abstractmethod
from typing import Any
import sys
_INFSTR = "1e" + repr(sys.float_info.max_10_exp + 1)

class Translator(ast.NodeVisitor, ABC):

    # class NodeVisitor:

    # def generic_visit(self, node):
    #     """Called if no explicit visitor function exists for a node."""
    #     for field, value in ast.iter_fields(node):
    #         if isinstance(value, list):
    #             for item in value:
    #                 if isinstance(item, ast.AST):
    #                     self.visit(item)
    #         elif isinstance(value, ast.AST):
    #             self.visit(value)

    def _visit(self, node):
        method = 'visit_' + node.__class__.__name__
        #print("_vist", method)
        if method == 'visit_Assign':
            return self.maybe_visit_sample(node)
        elif method == 'visit_Call':
            return self.maybe_visit_observe_factor(node)
        else:
            if not hasattr(self, method):
                print(ast.dump(node))
                raise Exception("Unsupported node " + node.__class__.__name__)
            visitor = getattr(self, method)
            return visitor(node)
        
    
    # Note: as visit() resets the output text, do NOT rely on
    # NodeVisitor.generic_visit to handle any nodes (as it calls back in to
    # the subclass visit() method, which resets self._source to an empty list)
    def visit(self, node):
        #print("visit")
        """Outputs a source code string that, if converted back to an ast
        (using ast.parse) will generate an AST equivalent to *node*"""
        self._source = []
        self.traverse(node)
        return "".join(self._source)

    def __init__(self):
        self._source = []
        self._precedences = {}
        
    def write(self, *text):
        """Add new source parts"""
        self._source.extend(text)
    
    def maybe_newline(self):
        """Adds a newline if it isn't the start of generated source"""
        if self._source:
            self.write("\n")

    def fill(self, text=""):
        """Indent a piece of text and append it, according to the current
        indentation level"""
        self.maybe_newline()
        self.write("    " * self._indent + text)

    def interleave(self, inter, f, seq):
        """Call f on each item in seq, calling inter() in between."""
        seq = iter(seq)
        try:
            f(next(seq))
        except StopIteration:
            pass
        else:
            for x in seq:
                inter()
                f(x)

    def items_view(self, traverser, items):
        """Traverse and separate the given *items* with a comma and append it to
        the buffer. If *items* is a single item sequence, a trailing comma
        will be added."""
        if len(items) == 1:
            traverser(items[0])
            self.write(",")
        else:
            self.interleave(lambda: self.write(", "), traverser, items)
    
    @abstractmethod
    @contextmanager
    def block(self):
        raise NotImplementedError
    
    @contextmanager
    def delimit(self, start, end):
        """A context manager for preparing the source for expressions. It adds
        *start* to the buffer and enters, after exit it adds *end*."""

        self.write(start)
        yield
        self.write(end)

    def delimit_if(self, start, end, condition):
        if condition:
            return self.delimit(start, end)
        else:
            return nullcontext()

    def require_parens(self, precedence, node):
        """Shortcut to adding precedence related parens"""
        return self.delimit_if("(", ")", self.get_precedence(node) > precedence)

    def get_precedence(self, node):
        return self._precedences.get(node, ast._Precedence.TEST)

    def set_precedence(self, precedence, *nodes):
        for node in nodes:
            self._precedences[node] = precedence

    def _write_arguments(self, args, keywords):
        with self.delimit("(", ")"):
            comma = False
            for e in args:
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)
            for e in keywords:
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)

    def traverse(self, node):
        if isinstance(node, list):
            for item in node:
                self.traverse(item)
        else:
            self._visit(node)
    

    # Probabilistic Program entry point
    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        match node:
            case ast.FunctionDef(
                name=probprog_name,
                args=ast.arguments(
                    args=probprog_args
                ),
                body=probprog_body,
                decorator_list=[
                    ast.Attribute(
                        attr='probabilistic_program'
                    )
                ]
            ):
                self.probprog(probprog_name, [arg.arg for arg in probprog_args], probprog_body)
    
            case _:
                raise Exception("Encountered FunctionDef that is not probabilistic program.")

    @abstractmethod
    def probprog(self, name: str, args: list[str], body):
        raise NotImplementedError
    
    def maybe_visit_sample(self, node):
        assert isinstance(node, ast.Assign)
        match node:
            case ast.Assign(
                targets=[target],
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id="pr"), attr="sample"),
                    args=[
                        address,
                        ast.Call(func=ast.Attribute(value=ast.Name(id="pr"), attr=distribution_name), args=distribution_args, keywords=distribution_keywords)
                    ]
                )
            ):
                self.probprog_sample(target, address, distribution_name, distribution_args, distribution_keywords)

            case _:
                self.visit_Assign(node)

    
    @abstractmethod
    def probprog_sample(self, target, address, distribution_name, distribution_args, distribution_keywords):
        raise NotImplementedError

    
    def maybe_visit_observe_factor(self, node):
        assert isinstance(node, ast.Call)
        match node:
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"), attr="observe"),
                    args=[
                        value,
                        address,
                        ast.Call(func=ast.Attribute(value=ast.Name(id="pr"), attr=distribution_name), args=distribution_args, keywords=distribution_keywords)
                    ]
            ):
                self.probprog_observe(value, address, distribution_name, distribution_args, distribution_keywords)

            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"), attr="observe"),
                    args=[
                        value,
                        address
                    ]
            ):
                self.probprog_boolean_observe(value, address)

            
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"), attr="factor"),
                    args=[
                        value
                    ]
            ):
                self.probprog_factor(value)

            case _:
                self.visit_Call(node)

    
    @abstractmethod
    def probprog_observe(self, value, address, distribution_name, distribution_args, distribution_keywords):
        raise NotImplementedError
    
    @abstractmethod
    def probprog_boolean_observe(self, value, address):
        raise NotImplementedError
    
    @abstractmethod
    def probprog_factor(self, value):
        raise NotImplementedError

class PythonTranslator(Translator):
    def __init__(self):
        super().__init__()
        self._indent = 0

    @contextmanager
    def block(self):
        """A context manager for preparing the source for blocks. It adds
        the character':', increases the indentation on enter and decreases
        the indentation on exit.
        """
        self.write(":")
        self._indent += 1
        yield
        self._indent -= 1

    def visit_Expr(self, node):
        self.fill()
        self.set_precedence(ast._Precedence.YIELD, node.value)
        self.traverse(node.value)
    
    def visit_Break(self, node):
        self.fill("break")

    def visit_Assign(self, node):
        self.fill()
        for target in node.targets:
            self.set_precedence(ast._Precedence.TUPLE, target)
            self.traverse(target)
            self.write(" = ")
        self.traverse(node.value)

    def visit_For(self, node):
        self.fill("for ")
        self.set_precedence(ast._Precedence.TUPLE, node.target)
        self.traverse(node.target)
        self.write(" in ")
        self.traverse(node.iter)
        with self.block():
            self.traverse(node.body)
        if node.orelse:
            self.fill("else")
            with self.block():
                self.traverse(node.orelse)

    def visit_If(self, node):
        self.fill("if ")
        self.traverse(node.test)
        with self.block():
            self.traverse(node.body)
        # collapse nested ifs into equivalent elifs.
        while node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            node = node.orelse[0]
            self.fill("elif ")
            self.traverse(node.test)
            with self.block():
                self.traverse(node.body)
        # final else
        if node.orelse:
            self.fill("else")
            with self.block():
                self.traverse(node.orelse)

    def visit_While(self, node):
        self.fill("while ")
        self.traverse(node.test)
        with self.block():
            self.traverse(node.body)
        if node.orelse:
            self.fill("else")
            with self.block():
                self.traverse(node.orelse)

    def visit_Name(self, node):
        self.write(node.id)

    def _write_constant(self, value):
        if isinstance(value, (float, complex)):
            # Substitute overflowing decimal literal for AST infinities,
            # and inf - inf for NaNs.
            # should not occur in practice
            self.write(
                repr(value)
                .replace("inf", _INFSTR)
                .replace("nan", f"({_INFSTR}-{_INFSTR})")
            )
        else:
            self.write(repr(value))

    def visit_Constant(self, node):
        value = node.value
        if isinstance(value, tuple):
            with self.delimit("(", ")"):
                self.items_view(self._write_constant, value)
        elif value is ...:
            self.write("...")
        else:
            if node.kind == "u":
                self.write("u")
            self._write_constant(node.value)

    def visit_List(self, node):
        with self.delimit("[", "]"):
            self.interleave(lambda: self.write(", "), self.traverse, node.elts)

    # value if test else other
    #def visit_IfExp(self, node):
    #    with self.require_parens(ast._Precedence.TEST, node):
    #        self.set_precedence(ast._Precedence.TEST.next(), node.body, node.test)
    #        self.traverse(node.body)
    #        self.write(" if ")
    #        self.traverse(node.test)
    #        self.write(" else ")
    #        self.set_precedence(ast._Precedence.TEST, node.orelse)
    #        self.traverse(node.orelse)
        
    def visit_Tuple(self, node):
        with self.delimit_if(
            "(",
            ")",
            len(node.elts) == 0 or self.get_precedence(node) > ast._Precedence.TUPLE
        ):
            self.items_view(self.traverse, node.elts)


    unop = {"Invert": "~", "Not": "not", "UAdd": "+", "USub": "-"}
    unop_precedence = {
        "not": ast._Precedence.NOT,
        "~": ast._Precedence.FACTOR,
        "+": ast._Precedence.FACTOR,
        "-": ast._Precedence.FACTOR,
    }

    def visit_UnaryOp(self, node):
        operator = self.unop[node.op.__class__.__name__]
        operator_precedence = self.unop_precedence[operator]
        with self.require_parens(operator_precedence, node):
            self.write(operator)
            # factor prefixes (+, -, ~) shouldn't be separated
            # from the value they belong, (e.g: +1 instead of + 1)
            if operator_precedence is not ast._Precedence.FACTOR:
                self.write(" ")
            self.set_precedence(operator_precedence, node.operand)
            self.traverse(node.operand)

    binop = {
        "Add": "+",
        "Sub": "-",
        "Mult": "*",
        "MatMult": "@",
        "Div": "/",
        "Mod": "%",
        "LShift": "<<",
        "RShift": ">>",
        "BitOr": "|",
        "BitXor": "^",
        "BitAnd": "&",
        "FloorDiv": "//",
        "Pow": "**",
    }

    binop_precedence = {
        "+": ast._Precedence.ARITH,
        "-": ast._Precedence.ARITH,
        "*": ast._Precedence.TERM,
        "@": ast._Precedence.TERM,
        "/": ast._Precedence.TERM,
        "%": ast._Precedence.TERM,
        "<<": ast._Precedence.SHIFT,
        ">>": ast._Precedence.SHIFT,
        "|": ast._Precedence.BOR,
        "^": ast._Precedence.BXOR,
        "&": ast._Precedence.BAND,
        "//": ast._Precedence.TERM,
        "**": ast._Precedence.POWER,
    }

    binop_rassoc = frozenset(("**",))
    def visit_BinOp(self, node):
        operator = self.binop[node.op.__class__.__name__]
        operator_precedence = self.binop_precedence[operator]
        with self.require_parens(operator_precedence, node):
            if operator in self.binop_rassoc:
                left_precedence = operator_precedence.next()
                right_precedence = operator_precedence
            else:
                left_precedence = operator_precedence
                right_precedence = operator_precedence.next()

            self.set_precedence(left_precedence, node.left)
            self.traverse(node.left)
            self.write(f" {operator} ")
            self.set_precedence(right_precedence, node.right)
            self.traverse(node.right)

    cmpops = {
        "Eq": "==",
        "NotEq": "!=",
        "Lt": "<",
        "LtE": "<=",
        "Gt": ">",
        "GtE": ">=",
        "Is": "is",
        "IsNot": "is not",
        "In": "in",
        "NotIn": "not in",
    }

    def visit_Compare(self, node):
        with self.require_parens(ast._Precedence.CMP, node):
            self.set_precedence(ast._Precedence.CMP.next(), node.left, *node.comparators)
            self.traverse(node.left)
            for o, e in zip(node.ops, node.comparators):
                self.write(" " + self.cmpops[o.__class__.__name__] + " ")
                self.traverse(e)

    boolops = {"And": "and", "Or": "or"}
    boolop_precedence = {"and": ast._Precedence.AND, "or": ast._Precedence.OR}

    def visit_BoolOp(self, node):
        operator = self.boolops[node.op.__class__.__name__]
        operator_precedence = self.boolop_precedence[operator]

        def increasing_level_traverse(node):
            nonlocal operator_precedence
            operator_precedence = operator_precedence.next()
            self.set_precedence(operator_precedence, node)
            self.traverse(node)

        with self.require_parens(operator_precedence, node):
            s = f" {operator} "
            self.interleave(lambda: self.write(s), increasing_level_traverse, node.values)

    def visit_Call(self, node):
        self.set_precedence(ast._Precedence.ATOM, node.func)
        self.traverse(node.func)
        with self.delimit("(", ")"):
            comma = False
            for e in node.args:
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)
            for e in node.keywords:
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)

    def visit_Subscript(self, node):
        def is_non_empty_tuple(slice_value):
            return (
                isinstance(slice_value, tuple)
                and slice_value.elts
            )

        self.set_precedence(ast._Precedence.ATOM, node.value)
        self.traverse(node.value)
        with self.delimit("[", "]"):
            if is_non_empty_tuple(node.slice):
                # parentheses can be omitted if the tuple isn't empty
                self.items_view(self.traverse, node.slice.elts)
            else:
                self.traverse(node.slice)

    def visit_Attribute(self, node):
        self.set_precedence(ast._Precedence.ATOM, node.value)
        self.traverse(node.value)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
            self.write(" ")
        self.write(".")
        self.write(node.attr)

    def visit_Return(self, node):
        self.fill("return")
        if node.value:
            self.write(" ")
            self.traverse(node.value)


class PyroTranslator(PythonTranslator):
    def visit_Call(self, node):
        match node:
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"),attr="IndexedAddress"),
                args = [ast.Constant(value=address), index]
                ):
                if isinstance(index, ast.Name):
                    self.write("f'" + address + "_{" + index.id + "}'")
                    return

        super().visit_Call(node)

    def probprog(self, name: str, args: list[str], body):
        self.write("import pyro\n")
        self.write("import pyro.distributions as dist\n")
        self.write(f"def {name}(", ", ".join(args), ")")
        with self.block():
            self.traverse(body)

    def probprog_sample(self, target, address, distribution_name, distribution_args, distribution_keywords):
        self.fill()
        self.set_precedence(ast._Precedence.TUPLE, target)
        self.traverse(target)
        self.write(" = pyro.sample(")
        self.traverse(address)
        self.write(f", dist.{distribution_name}")
        self._write_arguments(distribution_args, distribution_keywords)
        self.write(")")

    def probprog_observe(self, value, address, distribution_name, distribution_args, distribution_keywords):
        self.write("pyro.sample(")
        self.traverse(address)
        self.write(f", dist.{distribution_name}")
        self._write_arguments(distribution_args, distribution_keywords)
        self.write(", observed=")
        self.traverse(value)
        self.write(")")
    
    def probprog_boolean_observe(self, value, address):
        raise NotImplementedError
    
    def probprog_factor(self, value):
        raise NotImplementedError




#%%
import ast
s = """
@pr.probabilistic_program
def coin_flips(data):
    p = pr.sample("p", pr.Uniform(0, 1))
    for i in range(len(data)):
        pr.observe(data[i], pr.IndexedAddress("flip", i), pr.Bernoulli(p))
    return p
"""
# %%
a = ast.parse(s).body[0]
print(ast.dump(a, indent=2))
# %%
translator = PyroTranslator()
print(translator.visit(a))

# %%
