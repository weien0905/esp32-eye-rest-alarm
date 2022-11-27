"""Eye Rest Alarm"""

from machine import Pin
import time
import sys
import _thread

# Initialise pin setup
pir = Pin(14, Pin.IN)
led = Pin(2, Pin.OUT) # Built-in LED
buzzer = Pin(26, Pin.OUT)

state = 0
state2_time = 0
state0_time = 0

# Initialise work time and rest time settings from "time.txt"
with open("time.txt") as f:
    fcol, scol = f.read().split(",")
    work_time = int(fcol)
    rest_time = int(scol)

# Render web page that displays the current state, time left and current time settings
def web_page():
    html = """
<!DOCTYPE html><html lang="en"><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Eye Rest Alarm</title>
<style>h1,.center{text-align:center;}#min,#sec{font-size:60px;}#settings{text-align:center;margin:10px;}#settings div{margin:5px;}#rbtn{background-color:red;}a{text-decoration:none;color:white;}#sbtn{background-color:blue;color:white;}</style></head>
<body><h1>Eye Rest Alarm</h1><div class="center" id="state">%s</div><div class="center"><span id="min">%s</span><span>m</span> <span id="sec">%s</span><span>s</span></div><div class="center">
<button id="rbtn"><a href="reset">Reset</a></button></div><form id="settings">
<div>Work time: <input name="min" type="number" min="1" max="60" value="%s"> minutes</div>
<div>Rest time: <input name="sec" type="number" min="1" max="60" value="%s"> seconds</div><input type="submit" id="sbtn" value="Change & Reset"></form></body>
<script>let interval_id=null;const state=document.querySelector('#state');const minutes=document.querySelector('#min');const seconds=document.querySelector('#sec');document.addEventListener('DOMContentLoaded',start_timer());function start_timer(){interval_id=setInterval(()=>timer(),1000);};function timer(){if(parseInt(seconds.innerHTML)===0){if(parseInt(minutes.innerHTML)===0){clearInterval(interval_id);return;}minutes.textContent=parseInt(minutes.innerHTML)-1;seconds.textContent=59;return;}seconds.textContent=parseInt(seconds.innerHTML)-1;};
</script></html>"""
    if state == 0:
        text = "Not detected"
        min = 0
        sec = 0
    elif state == 1:
        diff = state2_time - time.ticks_ms()
        text = "Work time"
        sec = int(diff / 1000) % 60
        min = int((diff - sec) / 1000) / 60
    elif state == 2:
        diff = state0_time - time.ticks_ms()
        text = "Rest time"
        sec = int(diff / 1000) % 60
        min = int((diff - sec) / 1000) / 60
        
    return html % (text, int(min), int(sec), work_time, rest_time)
    
# Second thread (act as timer and change state based on the set time)
def second_thread():
    global state
    global state2_time
    global state0_time
    
    while True:
        current = time.ticks_ms()
        # Change state from "Not detected" to "Work time" when PIR sensor was triggered
        if state == 0 and pir.value():
            led.value(1)
            state = 1
            state2_time = current + ((work_time * 60) * 1000)
            state0_time = current + (((work_time * 60) + 1 + rest_time) * 1000)
        # Change state from "Work time" to "Rest time" when time is up
        elif state == 1 and current >= state2_time:
            led.value(0)
            buzzer.value(1)
            time.sleep(1)
            buzzer.value(0)
            state = 2
        # Change state from "Rest time" to "Not detected" when time is up
        elif state == 2 and current >= state0_time:
            state = 0

_thread.start_new_thread(second_thread, ())

# Main thread (web server)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 80))
s.listen(5)

while True:
    try:
        if gc.mem_free() < 102000:
            gc.collect()

        # Get request from user
        conn, addr = s.accept()
        request = conn.recv(1024)
        request = str(request)
        
        # Reset web page to initial state
        if request.find("/reset") != -1:
            state = 0
            led.value(0)

        # Get value from user and change time settings
        x = request.find("min=")
        y = request.find("sec=")
        if x != -1 and y != -1:
            work_time = int(request[x+4:x+6].replace("&", ""))
            rest_time = int(request[y+4:y+6].replace("\\", ""))
            with open("time.txt", "w") as f:
                f.write(str(work_time) + "," + str(rest_time))
            state = 0
            led.value(0)

        # Render success message if user choose to reset state, stop program or change time settings
        if request.find("/reset") != -1 or request.find("/stop") != -1 or (x != -1 and y != -1):
            response = "Success"
        # Render web page
        else:    
            response = web_page()
            
        # Return response to user
        conn.send("HTTP/1.1 200 OK\n")
        conn.send("Content-Type: text/html\n")
        conn.send("Connection: close\n\n")
        conn.sendall(response)
        conn.close()

        # Stop the program (in case KeyboardInterrupt is not functioning)
        if request.find("/stop") != -1:
            sys.exit()
    
    except OSError as e:
        conn.close()
        print(e)
