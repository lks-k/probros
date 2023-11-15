import ast
from julia_translator import JuliaTranslator

class GenTranslator(JuliaTranslator):
    def visit_Call(self, node):
        match node:
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"),attr="IndexedAddress"),
                args = [ast.Constant(value=address), index]
                ):
                if isinstance(index, ast.Name):
                    self.write(":" + address + " => " + index.id)
                    return

        super().visit_Call(node)

    def probprog(self, name: str, args: list[str], body):
        self.write("using Turing\n")
        self.write("using Distributions\n")
        self.write(f"@model function {name}(", ", ".join(args), ")")
        with self.block():
            self.traverse(body)

    def probprog_sample(self, target, address, distribution_name, distribution_args, distribution_keywords):
        self.fill()
        self.set_precedence(ast._Precedence.TUPLE, target)
        self.traverse(target)
        self.write(" = ")
        with self.delimit("{", "}"):
            self.traverse(address)
        self.write(" ~ ")
        self.write(f"{distribution_name}")
        self._write_arguments(distribution_args, distribution_keywords)

    def probprog_observe(self, value, address, distribution_name, distribution_args, distribution_keywords):
        with self.delimit("{", "}"):
            self.traverse(address)
        self.write(" ~ ")
        self.write(f"{distribution_name}")
        self._write_arguments(distribution_args, distribution_keywords)
    
    def probprog_boolean_observe(self, value, address):
        raise NotImplementedError
    
    def probprog_factor(self, value):
        raise NotImplementedError