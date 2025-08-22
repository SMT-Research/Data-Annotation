from base.analysis import Analyzer
from base.web import Server, InvertedGroup

from pathlib import Path
import numpy as np
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import struct
from scripts.model.model import model
import hashlib

DEAD_SIZE = timedelta(days=3)
HIGH_RES_PERIOD = timedelta(minutes=15)
SMOOTH_PERIOD = timedelta(days=1.5)
LOW_RES_PERIOD = timedelta(hours=6)

logging.basicConfig(
    level=logging.INFO, 
    format="(%(asctime)s) [%(levelname)s] [%(name)s] -> %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Sample Generator")

class Sample:
    def __init__(self):
        self.x: np.ndarray = None
        self.r1: np.ndarray = None
        self.r2: np.ndarray = None
        self.v1: np.ndarray = None
        self.v2: np.ndarray = None
        self.r1_id: int = None
        self.r2_id: int = None
        self.v1_id: int = None
        self.v2_id: int = None

    def to_bytes(self):
        buffer = b""
        buffer += struct.pack("IIII", self.r1_id, self.r2_id, self.v1_id, self.v2_id)
        buffer += self.x.tobytes()
        buffer += self.r1.tobytes()
        buffer += self.r2.tobytes()
        buffer += self.v1.tobytes()
        buffer += self.v2.tobytes()
        return buffer
    
class Inverted:
    def __init__(self):
        self.r1: Analyzer = None
        self.r2: Analyzer = None
        self.v1: Analyzer = None
        self.v2: Analyzer = None
    
    def download(r1: int, r2: int, v1: int, v2: int, server: Server, start_date: datetime, end_date: datetime):
        r1_raw = server.get_sensor_data(r1, start_date, end_date)
        r2_raw = server.get_sensor_data(r2, start_date, end_date)
        v1_raw = server.get_sensor_data(v1, start_date, end_date)
        v2_raw = server.get_sensor_data(v2, start_date, end_date)
        if(r1_raw == None or r2_raw == None or v1_raw == None or v2_raw == None):
            return None
        sensor = Inverted()
        sensor.r1 = Analyzer(np.array([x.timestamp() for x in r1_raw.time]), r1_raw.raw)
        sensor.r2 = Analyzer(np.array([x.timestamp() for x in r2_raw.time]), r2_raw.raw)
        sensor.v1 = Analyzer(np.array([x.timestamp() for x in v1_raw.time]), v1_raw.raw)
        sensor.v2 = Analyzer(np.array([x.timestamp() for x in v2_raw.time]), v2_raw.raw)
        return sensor

    def sensors(self):
        return [self.r1, self.r2, self.v1, self.v2]
    
    def preview(self):
        fig, axes = plt.subplots(2, 1, sharex=True)
        axes[0].plot(self.r1.x_data, self.r1.y_data)
        axes[0].plot(self.r2.x_data, self.r2.y_data)
        axes[1].plot(self.v1.x_data, self.v1.y_data)
        axes[1].plot(self.v2.x_data, self.v2.y_data)
        plt.show()

def download_project_samples(project_id, path, api="analytics2", start_date=datetime(2005, 1, 1), end_date=datetime.now()):
    logger.info("Logging in...")
    server = Server(f"https://{api}.smtresearch.ca/api/?")
    server.login("jennifer", "smt")

    logger.info("Fetching sensors...")
    sensors: list[InvertedGroup] = []
    for job in server.get_jobs(project_id):
        _, inverted = server.get_sensors(job.id)
        for sensor in inverted:
            if(not sensor in sensors):
                sensors.append(sensor)

    logger.info("Starting Download...")
    f = open(path, "wb")
    hashes = set()
    total_samples = 0
    for sensor in sensors:
        count_bytes = 0
        count_samples = 0
        sensor_data: Inverted = Inverted.download(sensor.r1.id, sensor.r2.id, sensor.v1.id, sensor.v2.id, server, start_date, end_date)
        if(sensor_data == None):
            logger.info(f"{sensor.name}: NO DATA, {count_samples} samples ({total_samples} total)")
        else:
            for analyzer in sensor_data.sensors():
                analyzer.sort()
                analyzer.make_continuous(p=HIGH_RES_PERIOD.total_seconds())
                analyzer.savitzky_golay(n=int(SMOOTH_PERIOD.total_seconds()/HIGH_RES_PERIOD.total_seconds()), poly_order=3)
                analyzer.make_continuous(p=LOW_RES_PERIOD.total_seconds())

            for t in range(
                int(min([x.x_data[0] for x in sensor_data.sensors()])),
                int(max([x.x_data[-1] for x in sensor_data.sensors()]) - model.INPUT_TIME.total_seconds()),
                int(model.INPUT_TIME.total_seconds() / 2)
            ):
                x_data = np.linspace(t, t+model.INPUT_TIME.total_seconds(), model.INPUT_SIZE)
                buffer = b""
                buffer += struct.pack("IIII", sensor.r1.id, sensor.r2.id, sensor.v1.id, sensor.v2.id)
                buffer += x_data.tobytes()
                for analyzer in sensor_data.sensors():
                    buffer += analyzer.f(x_data).tobytes()
                hash = hashlib.sha1(buffer).digest()[:8]
                buffer = hash + buffer
                if(not hash in hashes):
                    count_bytes += len(buffer)
                    count_samples += 1
                    total_samples += 1
                    hashes.add(hash)
                    f.write(buffer)
                else:
                    logger.warning("HASH COLLISION")

            logger.info(f"{sensor.name}: {count_bytes} bytes, {count_samples} samples ({total_samples} total)")

download_project_samples(456, "data/burquitlam", start_date=datetime(2010, 1, 1), end_date=datetime(2025, 1, 1))
# download_project_samples(440, "data/thepost1", server, start_date=datetime(2010, 1, 1), end_date=datetime(2025, 1, 1))
# download_project_samples(445, "data/oakridge", server, start_date=datetime(2010, 1, 1), end_date=datetime(2025, 1, 1))
# download_project_samples(552, "data/abbot", start_date=datetime(2010, 1, 1), end_date=datetime(2025, 1, 1))
# download_project_samples(488, "data/northharbour", start_date=datetime(2000, 1, 1), end_date=datetime(2025, 1, 1))