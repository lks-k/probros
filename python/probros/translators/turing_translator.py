import ast
from julia_translator import JuliaTranslator

class TuringTranslator(JuliaTranslator):
    def validate_indexed_address(self, address, target):
        match address:
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"),attr="IndexedAddress"),
                args = [ast.Constant(), *indexes]
                ):
                if not isinstance(target, ast.Subscript):
                        msg = "IndexedAddress used but value does not come from array.\n"
                        msg += f"{ast.unparse(address)} vs {ast.unparse(target)}"
                        raise Exception(msg)
                else:
                    if (isinstance(target.slice, ast.Tuple) and len(target.slice.elts) != len(indexes)) or (len(indexes) != 1):
                        msg = "Number of indices in IndexedAddress is not equal to number if indices in value.\n"
                        msg += f"{ast.unparse(address)} vs {ast.unparse(target)}"
                        raise Exception(msg)
                    
    def probprog(self, name: str, args: list[str], body):
        self.write("using Turing\n")
        self.write("using Distributions\n")
        self.write(f"@model function {name}(", ", ".join(args), ")")
        with self.block():
            self.traverse(body)

    def probprog_sample(self, target, address, distribution_name, distribution_args, distribution_keywords):
        self.validate_indexed_address(address, target)
        self.fill()
        self.set_precedence(ast._Precedence.TUPLE, target)
        self.traverse(target)
        self.write(" ~ ")
        #self.traverse(address)
        self.write(f"{distribution_name}")
        self._write_arguments(distribution_args, distribution_keywords)

    def probprog_observe(self, value, address, distribution_name, distribution_args, distribution_keywords):
        self.validate_indexed_address(address, value)
        self.traverse(value)
        self.write(" ~ ")
        # self.traverse(address)
        self.write(f"{distribution_name}")
        self._write_arguments(distribution_args, distribution_keywords)
    
    def probprog_boolean_observe(self, value, address):
        raise NotImplementedError
    
    def probprog_factor(self, value):
        raise NotImplementedError
    