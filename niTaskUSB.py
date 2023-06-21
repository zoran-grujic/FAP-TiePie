import nidaqmx
import time

times = []
for i in range(-10,10):
    times.append(time.time())
    print(times[-1])
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
        task.write(i, auto_start=True)

    time.sleep(.1)

to = times[0]
for t in times:
    print(t-to)
    to = t

times = []
with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
    for i in range(-10,10):
        times.append(time.time())
        print(times[-1])


        task.write(i, auto_start=True)

        time.sleep(.1)

to = times[0]
for t in times:
    print(t-to)
    to = t

