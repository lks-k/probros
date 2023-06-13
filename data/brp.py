"""
probprogs benchmark | brp.py

A variant of the bounded retransmission protocol (BRP). Tries to send `toSend`
number of packets via an unreliable channel. At most `maxFail` retransmissions
are attempted. `totalFail` marks the total number of failed attempts to send a
packet.

Leen Helmink, M. P. A. Sellink, Frits W. Vaandrager:
Proof-Checking a Data Link Protocol. TYPES 1993.
"""
import numpy as np
import time
from scipy.stats import bernoulli

np.random.seed(int(time.time()))

def brp(toSend: uint, maxFailed: uint) -> uint:
    """
    Properties:
        - send4
            type: uexp
            post: totalFailed
            pre: "[toSend <= 4] * (totalFailed + 1) + [toSend > 4] * \infty"
        - send10
            type: uexp
            post: totalFailed
            pre: "[toSend <= 10] * (totalFailed + 1) + [toSend > 10] * \infty"
    """
    sent: uint = 0
    failed: uint = 0
    totalFailed: uint = 0

    while failed < maxFailed and sent < toSend:
        """
        Hints:
            - send4:
                k-induction:
                    invariant: "[toSend <= 4] * (totalFailed + 1) + [toSend > 4] * \infty"
                    k: 5
            - send10:
                k-induction:
                    invariant: "[toSend <= 10] * (totalFailed + 1) + [toSend > 10] * \infty"
                    k: 11
        """
        if bernoulli(0.1).rvs():
            # successful transmission of current packet
            failed = 0
            sent = sent + 1
        else:
            # failed transmission of current packet
            failed = failed + 1
            totalFailed = totalFailed + 1

    return totalFailed
