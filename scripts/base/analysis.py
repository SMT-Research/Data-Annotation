from typing import Literal
import numpy as np
from scipy.signal import savgol_filter
import struct
from datetime import datetime

class Analyzer:
    x_data: np.ndarray = None
    y_data: np.ndarray = None
    is_sorted = False
    is_continuous = False

    def __init__(self, x_data: np.ndarray, y_data: np.ndarray):
        self.x_data = x_data
        self.y_data = y_data

    def sort(self):
        ind = self.x_data.argsort()
        self.x_data = np.take_along_axis(self.x_data, ind, 0)
        self.y_data = np.take_along_axis(self.y_data, ind, 0)
        self.is_sorted = True

    def make_continuous(self, n: int = 100, p=None):
        if(n <= 1):
            raise Exception("\"n\" must be greater than 1.")
        new_x = []
        new_y = []
        start_x = self.x_data[0]
        end_x = self.x_data[-1]
        if(p == None):
            p = (end_x-start_x)/n
        else:
            n = max(int((end_x-start_x)/p), 1)

        for i in range(n):
            new_x.append(start_x+p*i)
            new_y.append(self.f(start_x+p*i))

        self.x_data = np.array(new_x)
        self.y_data = np.array(new_y)
        self.is_continuous = True

    def force_deallocate(self):
        """This is for nuitka builds only, deallocates all nparrays.
        DO NOT USE UNLESS FIXING NUITKA MEMORY LEAKS."""
        self.x_data = None
        self.y_data = None
    
    def f(self, val, interpolation: Literal["linear", None] = "linear"):
        if(not self.is_sorted):
            raise Exception("Data must be sorted before indexing.")
        
        out = []

        is_iter = False
        itterator = iter([val])
        try:
            itterator = iter(val)
            is_iter = True
        except: pass

        for v in itterator:
            a = 0
            b = len(self.x_data)-1
            current_out = None
            while a != b-1:
                c = (b-a)//2+a
                if(self.x_data[c] == v):
                    current_out = self.y_data[c]
                    break
                elif(self.x_data[c] < v):
                    a = c
                elif(self.x_data[c] > v):
                    b = c
            if(current_out != None):
                out.append(current_out)
                continue

            if(interpolation == None):
                d_a = v-self.x_data[a]
                d_b = self.x_data[b]-v
                if(d_b < d_a):
                    out.append(self.y_data[b])
                else:
                    out.append(self.y_data[a])
            elif(interpolation == "linear"):
                x_a = self.x_data[a]
                x_b = self.x_data[b]
                y_a = self.y_data[a]
                y_b = self.y_data[b]
                if(x_a == x_b): out.append(y_b)
                else:
                    i = (v-x_a)/(x_b-x_a)
                    out.append((y_b-y_a)*i+y_a)
            else:
                raise Exception(f"Unkown interpolation algorithm \"{interpolation}\".")
        
        if(not is_iter):
            return out[0]
        return np.array(out)
        
    def save_data(self):
        return np.copy(self.x_data), np.copy(self.y_data)

    def discard_high_data(self, thresh=600_000_000):
        for i in range(len(self.y_data)):
            if(self.y_data[i] > thresh):
                self.y_data[i] = None
    
    def savitzky_golay(self, n: int = 40, x=None, poly_order=3):
        if(not self.is_continuous):
            raise Exception("Data must be continuous.")
        
        if(len(self.x_data) <= 1):
            return
        
        if(x != None):
            a = self.x_data[1] - self.x_data[0]
            n = x//a
        self.y_data = savgol_filter(self.y_data, min(n, len(self.y_data)), poly_order)

    def scale(self, multiplier):
        self.y_data = self.y_data / multiplier
    
    def to_bytes(self):
        return struct.pack("I", len(self.x_data)) + np.array([[x.timestamp() for x in self.x_data], self.y_data], dtype=np.float64).tobytes()
    
    def from_bytes(buffer: bytes):
        count = struct.unpack("I", buffer[:4])[0]
        data = np.frombuffer(buffer[4:], dtype=np.float64).reshape((2, count))
        analyzer = Analyzer([datetime.fromtimestamp(x) for x in data[0]], data[1])
        return analyzer