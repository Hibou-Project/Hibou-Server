import zmq
from src.settings import SETTINGS
from src.logger import CustomLogger

logger = CustomLogger("vision").get_logger()

class VideoStreamingPublisher:
    """
    Publisher for annotated frames on ZMQ socket.
    """
    def __init__(self):
        self.ctx = zmq.Context.instance()
        self.pub_socket_annotated = self.ctx.socket(zmq.PUB)
        self.pub_socket_annotated.bind(f"tcp://*:{SETTINGS.IPC_VIDEO_STREAMING_ANNOTATED_PORT}")
        logger.info(f"Video Streaming Publisher started on port {SETTINGS.IPC_VIDEO_STREAMING_ANNOTATED_PORT}")

    def publish(self, annotated_frame):
        self.pub_socket_annotated.send_pyobj(annotated_frame)

    def close(self):
        self.pub_socket_raw.close()
        self.pub_socket_annotated.close()
        self.ctx.term()