
#%%
#%load_ext autoreload
#%autoreload 2
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

print(20*"=", "Probros Program:", 20*"=")
print(s)

print("\n -> Translation to Pyro:\n")
translator = PyroTranslator()
print(translator.visit(a))

print("\n -> Translation to Turing:\n")
translator = TuringTranslator()
print(translator.visit(a))


print("\n -> Translation to Gen:\n")
translator = GenTranslator()
print(translator.visit(a))
#%%
# this program cannot be translated to Turing.jl
s = """
@pr.probabilistic_program
def geometric(p: float):
    i = 0
    while True:
        b = pr.sample(pr.IndexedAddress("b",i), pr.Bernoulli(p))
        if b == 1:
            break
        i = i + 1
    return i
"""
a = ast.parse(s).body[0]
print()
print(20*"=", "Probros Program:", 20*"=")
print(s)

print("\n -> Translation to Pyro:\n")
translator = PyroTranslator()
print(translator.visit(a))

print("\n -> Translation to Turing:\n")
try:
    translator = TuringTranslator()
    print(translator.visit(a))
except Exception as e:
    print(e)

print("\n -> Translation to Gen:\n")
translator = GenTranslator()
print(translator.visit(a))
#%%
# this program cannot be translated to Turing.jl
s = """
@pr.probabilistic_program
def gmm(K, data):
    p = pr.sample("p", pr.Uniform(0.,1.))
    mu = pr.Array((K,))
    for k in range(K):
        mu[k] = pr.sample(pr.IndexedAddress("mu",k), pr.Normal(0.,1.))
    
    z = pr.Vector(len(data))
    for i in range(len(data)):
        z[i] = pr.sample(pr.IndexedAddress("z",i), pr.Bernoulli(p))
        pr.observe(data[i], pr.IndexedAddress("y",i), pr.Normal(mu[z[i]],1.))

"""
a = ast.parse(s).body[0]
print()
print(20*"=", "Probros Program:", 20*"=")
print(s)

print("\n -> Translation to Pyro:\n")
translator = PyroTranslator()
print(translator.visit(a))

print("\n -> Translation to Turing:\n")
translator = TuringTranslator()
print(translator.visit(a))


print("\n -> Translation to Gen:\n")
translator = GenTranslator()
print(translator.visit(a))
