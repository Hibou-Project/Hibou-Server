from typing import Sequence

import numpy as np

from src.modules.audio.localization.data import MicInfo


class ConsensusOpeningStrategy:
    """
    Count time steps where the estimated angle falls in at least one mic opening
    that also has a positive drone inference. Emit the latest angle if enough
    frames agree (temporal consensus).
    """

    def __init__(
        self,
        mic_infos: list[MicInfo],
        opening: float,
        min_matching_frames: int = 2,
    ) -> None:
        mid = opening / 2
        self._ranges = [(mic.orientation - mid, mic.orientation + mid) for mic in mic_infos]
        self._min_matching_frames = min_matching_frames

    def decide(
        self,
        angles: Sequence[float],
        inferences: Sequence[Sequence[bool]],
    ) -> float:
        n = min(len(angles), len(inferences))
        if n == 0:
            return None

        angles_arr = np.asarray(angles[:n], dtype=np.float64)
        m = len(self._ranges)
        matching = np.zeros((n, m), dtype=bool)
        # print("--------------------------------")
        # print(angles_arr)
        # print(inferences)
        for i in range(n):
            angle = float(angles_arr[i])
            inst = inferences[i]
            for j, pred in enumerate(inst):
                if j >= m:
                    break
                lo, hi = self._ranges[j]
                if pred and lo <= angle <= hi:
                    matching[i, j] = True

        found = int(np.sum(np.any(matching, axis=1)))
        if found >= self._min_matching_frames:
            return float(angles[-1])
        return None
