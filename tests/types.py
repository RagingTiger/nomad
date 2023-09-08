"""Custom testing types."""
from typing import Optional
from typing import Tuple
from typing import Union


# type of input directly passed to cli options
ParamsInput = Union[str, int, float]

# type for all superset of all input testing: cli opts/args, and interactive
ParamsInputTest = Union[ParamsInput, Tuple[ParamsInput, ParamsInput]]

# type for args list passed to runner command used in cli testing
RunnerArgs = Optional[ParamsInputTest]
