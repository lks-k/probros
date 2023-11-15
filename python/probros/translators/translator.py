
# %%
# https://github.com/python/cpython/blob/3.12/Lib/ast.py
import ast
from contextlib import contextmanager, nullcontext
from abc import ABC, abstractmethod
from typing import Any

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
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
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