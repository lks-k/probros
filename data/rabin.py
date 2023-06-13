"""
probprogs benchmark | rabin.py

A variant of Rabin's mutual exclusion protocol [1] taken from [2]. We verify
that the probability of successfully selecting a unique winning process as at
least 2/3, independently of how many processes are contending for ownership of
the mutex.

[1]: Eyal Kushilevitz, Michael O. Rabin: Randomized Mutual Exclusion Algorithms Revisited.
[2]: Joe Hurd, Annabelle McIver, Carroll Morgan: Probabilistic Guarded Commands Mechanized in HOL. QAPL 2004.
"""
import numpy as np
import time
from scipy.stats import bernoulli

np.random.seed(int(time.time()))

def rabin(i: uint, n: uint) -> bool:
    """
    Properties:
        - successprob
            type: lexp
            post: [success]
            pre: "[1 == i] + [1 > i] * (2/3)"
    """
    while 1 < i:
        """
        Hints:
            - successprob:
                induction:
                    invariant: "([(0 <= n) && (n <= i)]) * (((2/3) * (1 - ((([i == n] * (n + 1)) * (2 ** -n)) + ([i == (n + 1)] * (2 ** -n))))) + ((([i == n] * n) * (2 ** -n)) + ([i == (n + 1)] * (2 ** -n))))"
        """
        n = i
        while 0 < n:
            d = 0 if bernoulli(0.5).rvs() else 1
            i = i - d
            n = n - 1

    success: bool = i == 1
    return success
