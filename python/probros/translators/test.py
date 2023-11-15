
#%%
%load_ext autoreload
%autoreload 2
import ast
from pyro_translator import PyroTranslator
from turing_translator import TuringTranslator
from gen_translator import GenTranslator

#%%
s = """
@pr.probabilistic_program
def coin_flips(data):
    p = pr.sample("p", pr.Uniform(0, 1))
    for i in range(len(data)):
        pr.observe(data[i], pr.IndexedAddress("flip", i), pr.Bernoulli(p))
    return p
"""
a = ast.parse(s).body[0]
print(ast.dump(a, indent=2))
# %%
translator = PyroTranslator()
print(translator.visit(a))

# %%
translator = TuringTranslator()
print(translator.visit(a))
# %%
translator = GenTranslator()
print(translator.visit(a))
# %%
