from src.modules.audio.localization.data import MicInfo

from src.modules.decision.strategies.base import DecisionStrategy
from src.modules.decision.strategies.consecutive_true import ConsecutiveTrueStrategy
from src.modules.decision.strategies.consensus_opening import ConsensusOpeningStrategy


def build_decision_strategy(
    name: str,
    mic_infos: list[MicInfo],
    opening: float,
    **kwargs,
) -> DecisionStrategy:
    key = name.strip().lower().replace("-", "_")
    if key == "consensus_opening":
        return ConsensusOpeningStrategy(mic_infos, opening, **kwargs)
    if key == "consecutive_true":
        return ConsecutiveTrueStrategy(mic_infos, opening, **kwargs)
    raise ValueError(f"Unknown decision strategy: {name!r}")


__all__ = [
    "DecisionStrategy",
    "ConsensusOpeningStrategy",
    "ConsecutiveTrueStrategy",
    "build_decision_strategy",
]
