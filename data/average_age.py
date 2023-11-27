"""
probprogs benchmark | average-age.py
Compute an average of input numbers (people's ages).
"""
import sys
sys.path.insert(0, '../python')
import probros as pr
from typing import List, Tuple
from functools import reduce

@pr.probabilistic_program
def average_age(names_and_ages: List[Tuple[str, float]]) -> float:
    ages = map(lambda x: x[1], names_and_ages)
    total_age = reduce(lambda acc, age: acc + age, ages, 0.0)
    return total_age / len(names_and_ages)
