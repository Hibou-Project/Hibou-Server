from typing import Sequence

from src.modules.audio.localization.data import MicInfo


class ConsecutiveTrueStrategy:
    """
    Require the last ``min_consecutive`` inference snapshots (oldest→newest in the
    buffer) to each have at least one ``True`` (drone on any mic). That is three
    consecutive “detection” frames in a row. If so, return the angle from the
    latest snapshot (``angles[-1]``).
    """

    def __init__(
        self,
        mic_infos: list[MicInfo],
        opening: float,
        min_consecutive: int = 3,
    ) -> None:
        self._min_consecutive = min_consecutive

    def decide(
        self,
        angles: Sequence[float],
        inferences: Sequence[Sequence[bool]],
    ) -> float | None:
        if not angles or not inferences:
            return None
        k = self._min_consecutive
        if len(inferences) < k or len(angles) < k:
            return None
        tail = inferences[-k:]
        if all(any(row) for row in tail):
            return float(angles[-1])
        return None
