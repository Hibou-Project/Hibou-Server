from typing import Protocol, Sequence, runtime_checkable


@runtime_checkable
class DecisionStrategy(Protocol):
    def decide(
        self,
        angles: Sequence[float],
        inferences: Sequence[Sequence[bool]],
    ) -> float | None: ...
