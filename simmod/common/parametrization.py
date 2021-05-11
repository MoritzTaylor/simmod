"""The parameterization is the connection between the setter functions, the simulation objects and their respective
value ranges. All those variables are stored in an individual parameterization instance.
"""
from abc import ABC
from typing import Union, List, Callable, AnyStr, Tuple, Any, Dict, Optional
from enum import Enum, auto

import numpy as np

Num = Union[int, float]
Array = Union[np.ndarray, List]
ArrayOrNum = Union[Array, Num]


class Execution(Enum):
    BEFORE_STEP = auto()
    AFTER_STEP = auto()
    RESET = auto()


class Parametrization:

    def __init__(
            self,
            setter: AnyStr,
            object_name: AnyStr,
            parameter_range: Array,
            execution: AnyStr,
            parameter_type: Optional[object] = None,  # TODO: Not used at the moment
            shape: Optional[Tuple] = None,
            name: Optional[AnyStr] = None
    ) -> None:
        self.setter = setter
        self.object_name = object_name
        self.execution = Execution[execution]
        if shape is not None:
            assert len(parameter_range) == 2 and shape[-1] == 2, \
                "If a shape is given the last dimension and the length of the range must match 2 (lower and higher bound)"
            self.shape = shape
            parameter_range = np.tile(parameter_range, (shape[0], 1))
        else:
            if not isinstance(parameter_range, np.ndarray):
                parameter_range = np.asarray(parameter_range)
            self.shape = parameter_range.shape
        self.lower_bound = parameter_range.T[0]
        self.upper_bound = parameter_range.T[1]
        self.name = name
        self.history = []
        self.current_val = None

    def __str__(self):
        return f'{self.setter}:{self.object_name}={self.current_val}'

    @property
    def parameter_range(self):
        return (self.lower_bound, self.upper_bound)

    def update(self, new_values, **kwargs):
        if self.current_val is not None:
            self.history.append(self.current_val)
        self.current_val = new_values

    def get_json(self) -> Dict:
        result = {
            self.setter: {
                self.object_name: self.current_val
            }
        }
        return result


class Parameter(ABC):

    def __init__(
            self,
            mod_func: Callable,
            init: Any
    ) -> None:
        self.mod_func = mod_func
        self.init = init


class Array(Parameter):

    def __init__(
            self,
            mod_func: Callable,
            init: Optional[ArrayOrNum] = None,
            lower: Optional[ArrayOrNum] = None,
            upper: Optional[ArrayOrNum] = None
    ) -> None:
        self.lower = lower
        self.upper = upper
        super().__init__(mod_func, init=init)


class Scalar(Array):

    def __init__(
            self,
            mod_func: Callable,
            init: Optional[Num] = None,
            lower: Num = 0,
            upper: Num = 1
    ) -> None:
        super().__init__(mod_func, init=np.array([init]), lower=np.array([lower]), upper=np.array([upper]))


class Boolean(Parameter):

    def __init__(
            self,
            mod_func: Callable,
            init: bool = True,
    ) -> None:
        super().__init__(mod_func, init=init)
