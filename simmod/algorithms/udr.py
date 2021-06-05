"""Uniform Domain Randomization (UDR) algorithm"""
from inspect import signature
from typing import Any, Union

import numpy as np
from numpy.random import default_rng, Generator

from simmod.utils.typings_ import *
from simmod.algorithms.base import BaseAlgorithm
from simmod.common.parametrization import Parametrization
from simmod.modification.base_modifier import BaseModifier
from simmod.common.parametrization import Execution

EXECUTION_POINTS = Union[Execution]


class UniformDomainRandomization(BaseAlgorithm):
    """
    Given a number of modifiers each with a number of instrumentations, the algorithm changes the parameters (specified
    in the instrumentation) of the underlying simulation. The simulation itself is not needed since it is connected
    via the modifiers.
    """

    def __init__(self, *modifiers: BaseModifier, random_state: Optional[Union[Generator, int]] = None,
                 **kwargs: Any) -> None:
        if random_state is None:
            self.random_state = default_rng()
        elif isinstance(random_state, int):
            # random_state assumed to be an int
            self.random_state = default_rng(random_state)
        elif isinstance(random_state, Generator):
            self.random_state = random_state
        else:
            raise ValueError(f"random_state argument must be either None, int or np.random.Generator, not {random_state}")
        super().__init__(*modifiers, **kwargs)

    def _randomize_object(self, modifier: BaseModifier, instrumentation: Parametrization, **kwargs) -> None:
        """Randomize the parameter of an object (both defined in the instrumentation variable) with
        the given modifier.

        The randomization is performed by sampling from a uniform distribution with upper and lower bounds defined in
        the instrumentation variable.

        Args:
            modifier: Modifier to change the parameter defined in the instrumentation
            instrumentation: Configuration of the parameter we want  change
            **kwargs: Additional arguments for the setter function of the modifier

        Returns:
            Return of the setter function of the modifier
        """
        object_name = instrumentation.object_name
        setter_func = modifier.standard_setters[instrumentation.setter]

        if setter_func.__defaults__ is not None:  # in case there are no kwargs
            n_kwargs = len(setter_func.__defaults__)
        else:
            n_kwargs = 0

        sig = signature(setter_func)
        n_params = len(sig.parameters) - n_kwargs - 1  # Exclude name & non-positional arguments
        # TODO: Randomize non-positional arguments

        x, y = instrumentation.parameter_values
        new_values = list()
        assert len(x) == len(y)
        n = len(x)
        for _ in range(n_params):
            dist = instrumentation.distribution
            if dist == 'uniform':
                values = np.array([self.random_state.uniform(x[i], y[i]) for i in range(n)])
            elif dist == 'normal' or dist == 'gaussian':
                values = np.array([self.random_state.normal(x[i], y[i]) for i in range(n)])
            elif dist == 'loguniform':
                values = np.exp([self.random_state.uniform(x[i], y[i]) for i in range(n)])
            else:
                raise ValueError(f"Distribution type '{dist}' not available, use 'uniform', 'loguniform' or 'normal'")
            new_values.append(values)
        instrumentation.update(new_values)
        return setter_func(object_name, *new_values, **kwargs)

    def step(self, execution: EXECUTION_POINTS = 'RESET', **kwargs) -> None:
        for modifier in self.modifiers:
            for instrumentation in modifier.instrumentation:
                self._randomize_object(modifier, instrumentation)
            modifier.update()
