from src.helpers.ipc.base_ipc import get_ipc_handler
from src.helpers.decorators import SingletonMeta
from src.logger import CustomLogger
from src.settings import SETTINGS
import datetime
import os
from collections import deque
import threading
from src.helpers.json import read_json
from pathlib import Path

from src.modules.audio.localization.data import MicInfo
from src.modules.decision.decision import DecisionMaker


logger = CustomLogger("decision").get_logger()


class DecisionWorker:
    def __init__(self, dt: datetime.datetime):
        logger.info(f"Started Decision Worker | PID: {os.getpid()}")

        self.ipc = get_ipc_handler()
        self.ipc.subscribe(SETTINGS.IPC_ACOUSTIC_DETECTION_TOPIC, self._update_audio_inf)
        self.ipc.subscribe(SETTINGS.IPC_ACOUSTIC_ANGLE_TOPIC, self._update_audio_angle)

        self.angles = deque(maxlen=3)
        self.inferences = deque(maxlen=3)

        self._updated = False
        self._condition = threading.Condition()

        mic_data = read_json(Path("./mic_information.json"))
        mic_array = mic_data["array"]
        self.mic_infos = [
            MicInfo.from_dict(info)
            for info in mic_array
        ]

        self._dm = DecisionMaker(self.angles, self.inferences, self.mic_infos, mic_data["opening"])

        try:
            self.run()
        except KeyboardInterrupt:
            logger.critical("Stopping Decision Worker...")
        finally:
            SingletonMeta.clear()

    def _update_audio_inf(self, topic: str, values: str):
        predictions = [bool(v) for v in values.split(",") if len(v) != 0]

        with self._condition:
            self.inferences.append(predictions)
            self._updated = True
            self._condition.notify()

    def _update_audio_angle(self, topic: str, angle: str):
        with self._condition:
            self.angles.append(float(angle))
            self._updated = True
            self._condition.notify()

    def run(self):
        logger.info("Running decision worker...")
        while True:
            with self._condition:
                while not self._updated or len(self.inferences) < 3 or len(self.angles) < 3:
                    self._condition.wait()

                self._updated = False

                angle = self._dm.update()
                self.ipc.publish(SETTINGS.IPC_DECISION_ANGLE_TOPIC, f"{angle}")
                print(angle)
