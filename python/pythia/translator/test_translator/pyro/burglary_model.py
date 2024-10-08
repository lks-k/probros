# Translated code start.
import pyro
import pyro.distributions as dist
import torch
def burglary_model(data):
    earthquake = pyro.sample('earthquake', dist.Bernoulli(0.02))
    burglary = pyro.sample('burglary', dist.Bernoulli(0.01))
    if (earthquake) == (1):
        phone_working = pyro.sample('phone_working', dist.Bernoulli(0.8))
    else:
        phone_working = pyro.sample('phone_working', dist.Bernoulli(0.9))
    if (earthquake) == (1):
        mary_wakes = pyro.sample('mary_wakes', dist.Bernoulli(0.8))
    else:
        if (burglary) == (1):
            mary_wakes = pyro.sample('mary_wakes', dist.Bernoulli(0.7))
        else:
            mary_wakes = pyro.sample('mary_wakes', dist.Bernoulli(0.1))
    called = ((mary_wakes) == (1)) and ((phone_working) == (1))
    pyro.sample('observed', dist.Delta(torch.tensor(called)), obs=data)
# Translated code end.
# FIXME: Pyro's sample with Bernoulli sometimes returns multiple values. Making
# this fail. Maybe because of "when any sample statement is observed, the
# cumulative effect of every other sample statement in a model changes"? (See:
# https://pyro.ai/examples/intro_long.html#Background:-the-pyro.sample-primitive)
# Or NUTS and HMC only work for continuous variables? (See:
# https://pyro.ai/examples/enumeration.html) Also tried
# `@infer_discrete(first_available_dim=-1)` but didn't work either.
data = torch.tensor(True)
kernel = pyro.infer.NUTS(burglary_model)
mcmc = pyro.infer.MCMC(kernel, num_samples=1000, warmup_steps=100)
mcmc.run(data)
print("Inferred:")
samples = mcmc.get_samples()
print(f"\tearthquake={samples["earthquake"].mean(0)}")
print(f"\tburglary={samples["burglary"].mean(0)}")
print(f"\tphone_working={samples["phone_working"].mean(0)}")
print(f"\tmary_wakes={samples["mary_wakes"].mean(0)}")
