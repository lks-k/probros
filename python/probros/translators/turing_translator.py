import ast
from julia_translator import JuliaTranslator

class TuringTranslator(JuliaTranslator):
    def probprog(self, name: str, args: list[str], body):
        self.write("using Turing\n")
        self.write("using Distributions\n")
        self.write(f"@model function {name}(", ", ".join(args), ")")
        with self.block():
            self.traverse(body)

    def probprog_sample(self, target, address, distribution_name, distribution_args, distribution_keywords):
        # TODO: fail if indexedaddress but not indexed target
        self.fill()
        self.set_precedence(ast._Precedence.TUPLE, target)
        self.traverse(target)
        self.write(" ~ ")
        #self.traverse(address)
        self.write(f"{distribution_name}")
        self._write_arguments(distribution_args, distribution_keywords)

    def probprog_observe(self, value, address, distribution_name, distribution_args, distribution_keywords):
        self.traverse(value)
        self.write(" ~ ")
        # self.traverse(address)
        self.write(f"{distribution_name}")
        self._write_arguments(distribution_args, distribution_keywords)
    
    def probprog_boolean_observe(self, value, address):
        raise NotImplementedError
    
    def probprog_factor(self, value):
        raise NotImplementedError
    