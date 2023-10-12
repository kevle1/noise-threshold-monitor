import csv
import datetime
import pyaudio
import math
import struct
import wave
import time
import os

Threshold = 120

SHORT_NORMALIZE = 1.0 / 32768.0

OUTPUT = "./recordings"

if not os.path.exists(OUTPUT):
    os.makedirs(OUTPUT)

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 30

chunk = 1024
swidth = 2


class Recorder:
    @staticmethod
    def rms(frame):
        count = len(frame) / swidth
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.list_device_indexes()

        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            # input_device_index=1, # Set only if required
            output=True,
            frames_per_buffer=chunk,
        )

    def list_device_indexes(self) -> int:
        print("Available Audio Input Devices:")
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            device_name = device_info["name"]
            print(f"Index {i}: {device_name}")

    def record(self, start_time: datetime.datetime):
        print(f"Recording beginning at {start_time}.")
        rec = []
        current = time.time()
        end = time.time() + RECORD_SECONDS

        while current <= end:
            data = self.stream.read(chunk)
            if self.rms(data) >= Threshold:
                end = time.time() + RECORD_SECONDS
            current = time.time()
            rec.append(data)

        self.write(start_time, b"".join(rec))

    def write(self, start_time: datetime.datetime, recording: bytes):
        filename = os.path.join(
            OUTPUT, f"{start_time.strftime('%Y-%m-%d-%H-%M-%S')}.wav"
        )

        wf = wave.open(filename, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(recording)
        wf.close()

        print(f"Written to file: {filename}")
        print("Resuming monitoring")

    def log(self, start_time: datetime.datetime):
        filename = os.path.join(OUTPUT, f"log.csv")
        with open(filename, mode="a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(
                [start_time.strftime("%Y-%m-%d"), start_time.strftime("%H:%M:%S")]
            )

    def listen(self):
        print("Beginning monitoring")
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)
            if rms_val > Threshold:
                start_time = datetime.datetime.now()
                print("Exceeded threshold")
                self.record(start_time)
                self.log(start_time)


a = Recorder()
a.listen()
