import ast
from python_translator import PythonTranslator

class PyroTranslator(PythonTranslator):
    def visit_Call(self, node):
        match node:
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"),attr="IndexedAddress"),
                args = [ast.Constant(value=address), *indexes]
                ):
                pyro_address = "f'" + address + "_{"
                ids = []
                for index in indexes:
                    if isinstance(index, ast.Name):
                        ids.append(str(index.id))
                pyro_address += ",".join(ids) + "}'"
                self.write(pyro_address)
            
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"),attr="Vector"),
                args = [size] # TODO: optional type and fill parameter
                ):
                with self.delimit("torch.zeros((", ",))"):
                    self.traverse(size)
            
            case ast.Call(
                func=ast.Attribute(value=ast.Name(id="pr"),attr="Array"),
                args = [shape] # TODO: optional type and fill parameter
                ):
                with self.delimit("torch.zeros(", ")"):
                    self.traverse(shape)

            case _:
                super().visit_Call(node)

    def probprog(self, name: str, args: list[str], body):
        self.write("import torch\n")
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
