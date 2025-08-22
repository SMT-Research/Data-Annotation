import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date
import numpy as np
import logging
from time import sleep
from urllib.parse import urlparse, urlunparse
from enum import Enum
from io import BytesIO
from PIL import Image

logger = logging.getLogger("Talaria Web")

def strip_url_subdirectories(url):
    parsed_url = urlparse(url)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))

class ProjectInfo:
    id: int = None
    name: str = None
    def __init__(self, id:int, name:str):
        self.id = id
        self.name = name
    def __str__(self):
        return f"{self.name} ({self.id})"

class JobInfo:
    id: int = None
    name: str = None
    def __init__(self, id:int, name:str):
        self.id = id
        self.name = name
    def __str__(self):
        return f"{self.name} ({self.id})"

class SensorInfo:
    id: int = None
    name: str = None
    creation_date: datetime = None
    modified_date: datetime = None
    is_inverted: bool = False
    def __init__(self, id:int, name:str, creation_date:datetime, modified_date:datetime):
        self.id = id
        self.name = name
        self.creation_date = creation_date
        self.modified_date = modified_date
    def __eq__(self, other):
        if(not type(other) is type(self)):
            return False
        return self.id == other.id
    def __str__(self):
        return self.name
    
class InvertedGroup:
    name: str = None
    job_id: int = None
    r1: SensorInfo = None
    r2: SensorInfo = None
    v1: SensorInfo = None
    v2: SensorInfo = None

    def __init__(self, name, job_id):
        self.name = name
        self.job_id = job_id
    
    def is_valid(self) -> bool:
        return (self.r1 != None) and (self.r2 != None) and (self.v1 != None) and (self.v2 != None)
    
    def as_list(self) -> list[SensorInfo]:
        return [
            self.r1,
            self.r2,
            self.v1,
            self.v2,
        ]
    
    def __getitem__(self, key: str):
        if(key == "r1"): return self.r1
        if(key == "r2"): return self.r2
        if(key == "v1"): return self.v1
        if(key == "v2"): return self.v2

    def __setitem__(self, key: str, value: SensorInfo):
        if(key == "r1"):
            self.r1 = value
        elif(key == "r2"):
            self.r2 = value
        elif(key == "v1"):
            self.v1 = value
        elif(key == "v2"):
            self.v2 = value

    def __eq__(self, other):
        if(not type(other) is type(self)):
            return False
        if(self.r1 == other.r1 and 
           self.r2 == other.r2 and 
           self.v1 == other.v1 and
           self.v2 == other.v2):
            return True
        return False 

class SensorData:
    raw: np.ndarray[np.int32] = None
    eng_unit: np.ndarray[np.float32] = None
    time: np.ndarray[datetime] = None

class AlarmData:
    sensor_id: int = None
    triggered: datetime = None
    cleared: datetime = None

class DrawingInfo:
    id: int
    name: str = None
    image: bytearray = None

class DrawingSensorType(Enum):
    TAPE = 0
    WIDAQ = 1
    ELLIPSE = 2
    RECTANGLE = 3
    WATER_DROP = 4

class DrawingSensor:
    id: int
    type: DrawingSensorType
    start_x: int
    start_y: int
    end_x: int
    end_y: int

class Server:
    api = "https://analytics2.smtresearch.ca/api/?"
    domain = strip_url_subdirectories(api)

    session: requests.Session = requests.Session()
    domain_session: requests.Session = requests.Session()
        
    def __init__(self, api: str = "https://analytics2.smtresearch.ca/api/?"):
        self.api = api

    def domain_request(self, path) -> requests.Response:
        url = self.domain + path
        failed = False
        while True:
            try:
                r = self.domain_session.get(url, timeout=60)
                break
            except requests.RequestException as e:
                if(not failed):
                    logger.error("Connection failed, attempting to reconnect.")
                    failed = True
                sleep(5)
        if(failed):
            logger.info("Reconnected successfully.")
        return r
    
    def request(self, action: str, **kwargs) -> ET.ElementTree:
        url = f"{self.api}action={action}&{'&'.join([f'{n}={kwargs[n]}' for n in kwargs])}"
        logger.debug(url)
        failed = False
        while True:
            try:
                r = self.session.get(url, timeout=60)
                xml = ET.ElementTree(ET.fromstring(r.content)).getroot()
                break
            except requests.RequestException as e:
                if(not failed):
                    logger.error("Connection failed, attempting to reconnect.")
                    failed = True
                sleep(5)
        if(failed):
            logger.info("Reconnected successfully.")
        return xml
    
    def login(self, username, password):
        xml = self.request("login", user_username=username, user_password=password)
        if(xml.find("error") != None):
            raise Exception("Login failed.")
        
        r = self.domain_session.post("https://analytics2.smtresearch.ca/", data={
            "action": "login",
            "user_username": username,
            "user_password": password,
        })
    
    def get_projects(self) -> list[ProjectInfo]:
        projects = []
        xml = self.request("listProject")
        for project in xml.findall("projects/"):
            projects.append(ProjectInfo(int(project.findtext("projectID")), project.findtext("name")))
        return projects

    def get_jobs(self, project_id: int) -> list[JobInfo]:
        jobs = []
        xml = self.request("listJob", projectID=project_id)
        for job in xml.findall("jobs/"):
            jobs.append(JobInfo(int(job.findtext("jobID")), job.findtext("name")))
        return jobs

    def get_sensors_legacy(self, job_id: int) -> list[SensorInfo]:
        sensors = []
        node_xml = self.request("listNode", jobID=job_id)
        for node in node_xml.findall("nodes/"):
            node_id = int(node.findtext("nodeID"))
            sensor_xml = self.request("listSensor", nodeID=node_id)
            for sensor in sensor_xml.findall("sensors/"):
                creation_date = datetime.strptime(sensor.findtext("created"), "%Y-%m-%d %H:%M:%S")
                modified_date = datetime.strptime(sensor.findtext("modified"), "%Y-%m-%d %H:%M:%S")
                sensors.append(SensorInfo(int(sensor.findtext("sensorID")), sensor.findtext("name"), creation_date, modified_date))
        return sensors

    def get_sensors(self, job_id: int) -> tuple[list[SensorInfo], list[InvertedGroup]]:
        inverted_groups: list[InvertedGroup] = []
        all_sensors = []
        node_xml = self.request("listNode", jobID=job_id)
        for node in node_xml.findall("nodes/"):
            node_id = int(node.findtext("nodeID"))
            sensor_xml = self.request("listSensor", nodeID=node_id)
            for sensor_element in sensor_xml.findall("sensors/"):
                creation_date = datetime.strptime(sensor_element.findtext("created"), "%Y-%m-%d %H:%M:%S")
                modified_date = datetime.strptime(sensor_element.findtext("modified"), "%Y-%m-%d %H:%M:%S")
                sensor_id = int(sensor_element.findtext("sensorID"))
                sensor_name = sensor_element.findtext("name")
                sensor = SensorInfo(sensor_id, sensor_name, creation_date, modified_date)
                all_sensors.append(sensor)

                if(len(sensor.name) >= 2):
                    suffix = sensor.name[-2:].lower()
                    prefix = sensor.name[:-2].strip()
                    if(suffix in ["v1", "v2", "r1", "r2"]):
                        for group in inverted_groups:
                            if(group.name == prefix):
                                group[suffix] = sensor
                                break
                        else:
                            new_group = InvertedGroup(prefix, job_id)
                            new_group[suffix] = sensor
                            inverted_groups.append(new_group)

        i = 0
        while i < len(inverted_groups):
            group = inverted_groups[i]
            if(group.is_valid()):
                group.r1.is_inverted = True
                group.r2.is_inverted = True
                group.v1.is_inverted = True
                group.v2.is_inverted = True
                i += 1
            else:
                inverted_groups.pop(i)
        
        return (all_sensors, inverted_groups)

    def get_sensor_data(self, sensor_id: int, start_date: date, end_date: date) -> SensorData:
        data = SensorData()
        try:
            xml = self.request("listSensorData", sensorID=sensor_id, startDate=start_date.strftime('%Y-%m-%d'), endDate=end_date.strftime('%Y-%m-%d'))
        except:
            return None
        raws = []
        eng_units = []
        times = []
        for entry in xml.findall("readings/"):
            try:
                raw = int(entry.findtext("raw"))
                eng_unit = float(entry.findtext("engUnit"))
                time = datetime.strptime(entry.findtext("timestamp"), "%Y-%m-%d %H:%M:%S")
                raws.append(raw)
                eng_units.append(eng_unit)
                times.append(time)
            except:
                pass
        if(len(raws) == 0 or len(eng_units) == 0 or len(times) == 0):
            return None
        data.raw = np.array(raws, dtype=np.float64)
        data.eng_unit = np.array(eng_units, dtype=np.float64)
        data.time = np.array(times)
        return data
    
    def get_alarm_data(self, sensor_id: int, start_time: datetime, end_time: datetime, job_id:int=None) -> list[AlarmData]:
        alarms = []
        if(job_id != None):
            xml = self.request("listAlarmInstances", jobID=job_id, startTime=start_time.strftime("%Y-%m-%d_%H:%M:%S"), endTime=end_time.strftime("%Y-%m-%d_%H:%M:%S"))
        else:
            xml = self.request("listAlarmInstances", sensorID=sensor_id, startTime=start_time.strftime("%Y-%m-%d_%H:%M:%S"), endTime=end_time.strftime("%Y-%m-%d_%H:%M:%S"))

        for alarm_state in xml.findall("tms/"):
            alarm = AlarmData()
            alarm.sensor_id = int(alarm_state.findtext("sensorID"))
            triggered_text = alarm_state.findtext("TriggeredUTC").replace("+00", "")
            cleared_text = alarm_state.findtext("ClearedUTC").replace("+00", "")
            if(triggered_text != ""): alarm.triggered = datetime.strptime(triggered_text, "%Y-%m-%d %H:%M:%S")
            if(cleared_text != ""): alarm.triggered = datetime.strptime(cleared_text, "%Y-%m-%d %H:%M:%S")
            alarms.append(alarm)
        return alarms
    
    def get_earliest_timestamp(self, project_id: int):
        # https://reproduction.smtresearch.ca/api/?action=getEarliestTimestamp&projectID=358
        xml = self.request("getEarliestTimestamp", projectID=project_id)
        date = datetime.fromisoformat(xml.findall("projects/")[0].findtext("ts"))
        return date
    
    def get_drawings(self, job_id: int) -> list[DrawingInfo]:
        xml = self.request("getdID", jobID=job_id)

        drawings = []
        for drawing in xml.findall("dIDs/"):
            drawing_data = DrawingInfo()
            drawing_data.id = int(drawing.findtext("dID"))
            drawing_data.name = drawing.findtext("title")
            drawing_data.image = drawing.findtext("drawingData")
            drawings.append(drawing_data)

        return drawings
    
    def get_drawing_sensors(self, drawing_id: int) -> list[DrawingSensor]:
        xml = self.request("getDataForUnity", dID=drawing_id)

        sensors = []
        for sensor in xml.findall("sensors/"):
            ds = DrawingSensor()
            ds.id = int(sensor.findtext("sensorID"))
            ds.type = DrawingSensorType(int(sensor.findtext("type")))
            ds.start_x = int(sensor.findtext("startx"))
            ds.start_y = int(sensor.findtext("starty"))
            ds.end_x = int(sensor.findtext("endx"))
            ds.end_y = int(sensor.findtext("endy"))
            sensors.append(ds)

        return sensors
    
    def get_drawing_image(self, drawing_id: int):
        try:
            r = self.domain_request(f"/drawings/drawing.php?dID={drawing_id}&showSensors=0")
            image_buffer = BytesIO(r.content)
            image = Image.open(image_buffer)
            return image
        except Image.DecompressionBombError:
            logger.warning("Drawing was too large, downscaling.")
            r = self.domain_request(f"/drawings/drawing.php?dID={drawing_id}&showSensors=0&forcesize=1")
            image_buffer = BytesIO(r.content)
            image = Image.open(image_buffer)
            return image
        except:
            return None