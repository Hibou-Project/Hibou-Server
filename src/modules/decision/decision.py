from collections import deque
import numpy as np

from src.modules.audio.localization.data import MicInfo


class DecisionMaker:
    def __init__(self, angles: deque[float], inferences: deque[list[bool]], mic_infos: list[MicInfo], opening: float) -> None:
        mid = opening/2

        self._angles = angles
        self._inferences = inferences
        self._ranges = [(mic.orientation - mid, mic.orientation + mid) for mic in mic_infos]

    def update(self) -> float:
        angles = np.array(self._angles)
        inferences = np.array(self._inferences)

        matching_openings = [[False] * len(self._ranges)] * len(self._ranges)
        for i, inst in enumerate(inferences):
            angle = angles[i]

            for j, pred in enumerate(inst):
                if pred and  angle <= self._ranges[j][1] and self._ranges[j][0] <= angle:
                    matching_openings[i][j] = True

        found = np.sum([int(np.any(l)) for l in matching_openings])

        # We set a threshold of at least 2 matching angles with the inferences.
        return self._angles[-1] if found > 1 else np.nan
