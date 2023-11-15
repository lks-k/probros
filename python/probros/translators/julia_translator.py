from translator import Translator
import ast
from contextlib import contextmanager
import sys
_INFSTR = "1e" + repr(sys.float_info.max_10_exp + 1)

class JuliaTranslator(Translator):
    def __init__(self):
        super().__init__()
        self._indent = 0

    @contextmanager
    def block(self, write_end=True):
        """A context manager for preparing the source for blocks. It adds
        the character':', increases the indentation on enter and decreases
        the indentation on exit.
        """
        self._indent += 1
        yield
        self._indent -= 1
        if write_end:
            self.fill("end")

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
        match node.iter:
            case ast.Call(
                    func=ast.Name(id="range"),
                    args=[end_iter]
                ):
                    self.write("0:")
                    self.traverse(end_iter)
                    self.write("-1")
            case ast.Call(
                    func=ast.Name(id="range"),
                    args=[start_iter, end_iter]
                ):
                    self.traverse(start_iter)
                    self.write(":")
                    self.traverse(end_iter)
                    self.write("-1")
            case _:
                raise Exception(f"Unsupported for loop range {ast.dump(node.iter)}")
        with self.block():
            self.traverse(node.body)

    def visit_If(self, node):
        self.fill("if ")
        self.traverse(node.test)
        with self.block(write_end=node.orelse==[]):
            self.traverse(node.body)
        # collapse nested ifs into equivalent elifs.
        while node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            node = node.orelse[0]
            self.fill("elseif ")
            self.traverse(node.test)
            with self.block(write_end = not (node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If))):
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
        elif isinstance(value, bool):
            self.write(repr(value).lower())
        elif isinstance(value, str):
            self.write('"' + repr(value)[1:-1] + '"')
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


    unop = {
        "Invert": ("~", ast._Precedence.NOT),
        "Not": ("!", ast._Precedence.FACTOR),
        "UAdd": ("+", ast._Precedence.FACTOR),
        "USub": ("-", ast._Precedence.FACTOR)
    }

    def visit_UnaryOp(self, node):
        operator, operator_precedence = self.unop[node.op.__class__.__name__]
        with self.require_parens(operator_precedence, node):
            self.write(operator)
            # factor prefixes (+, -, ~) shouldn't be separated
            # from the value they belong, (e.g: +1 instead of + 1)
            if operator_precedence is not ast._Precedence.FACTOR:
                self.write(" ")
            self.set_precedence(operator_precedence, node.operand)
            self.traverse(node.operand)

    binop = {
        "Add": ("+", ast._Precedence.ARITH),
        "Sub": ("-", ast._Precedence.ARITH),
        "Mult": ("*", ast._Precedence.TERM),
        "Div": ("/", ast._Precedence.TERM),
        "Mod": ("%", ast._Precedence.TERM),
        "BitOr": ("|", ast._Precedence.BOR),
        "BitXor": ("^", ast._Precedence.BXOR),
        "BitAnd": ("&", ast._Precedence.BAND),
        "Pow": ("^", ast._Precedence.POWER),
    }

    binop_rassoc = frozenset(("^",))
    def visit_BinOp(self, node):
        operator, operator_precedence = self.binop[node.op.__class__.__name__]
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
    }

    def visit_Compare(self, node):
        with self.require_parens(ast._Precedence.CMP, node):
            self.set_precedence(ast._Precedence.CMP.next(), node.left, *node.comparators)
            self.traverse(node.left)
            for o, e in zip(node.ops, node.comparators):
                self.write(" " + self.cmpops[o.__class__.__name__] + " ")
                self.traverse(e)

    boolops = {
        "And": ("&&", ast._Precedence.AND),
        "Or": ("||", ast._Precedence.OR)
    }

    def visit_BoolOp(self, node):
        operator, operator_precedence = self.boolops[node.op.__class__.__name__]

        def increasing_level_traverse(node):
            nonlocal operator_precedence
            operator_precedence = operator_precedence.next()
            self.set_precedence(operator_precedence, node)
            self.traverse(node)

        with self.require_parens(operator_precedence, node):
            s = f" {operator} "
            self.interleave(lambda: self.write(s), increasing_level_traverse, node.values)


    def visit_Call(self, node):
        match node:
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"),attr="Vector"),
                args = [size] # TODO: optional type and fill parameter
                ):
                with self.delimit("zeros(", ")"):
                    self.traverse(size)
                return
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"),attr="Array"),
                args = [shape] # TODO: optional type and fill parameter
                ):
                with self.delimit("zeros(", ")"):
                    self.traverse(shape)
                return


        self.set_precedence(ast._Precedence.ATOM, node.func)
        match node.func:
            case ast.Name(id=func_name):
                if func_name == "len":
                    self.write("length")
                else:
                    self.write(func_name)
            case _:
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
                isinstance(slice_value, ast.Tuple)
                and slice_value.elts
            )
        def traverser(node):
            self.traverse(node)
            self.write("+1")

        self.set_precedence(ast._Precedence.ATOM, node.value)
        self.traverse(node.value)
        with self.delimit("[", "]"):
            if is_non_empty_tuple(node.slice):
                # parentheses can be omitted if the tuple isn't empty
                self.items_view(traverser, node.slice.elts)
            elif isinstance(node.slice, ast.Name):
                self.write(node.slice.id, "+1")
            else:
                # TODO
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