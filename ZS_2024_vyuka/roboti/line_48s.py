# 48s
'''
Example program of a simple line follower robot with 2 motors, 1 OC RGB sensor using a PID regulator.
Fill TODO parts with your own code.
'''
import time

from lib.robot_consts import Button, Port, Sensor, Light

# TODO Change these constants
REGULATION_PERIOD_MS = 5       # Regulation period 0.01 s <=> 100 Hz
MOTOR_BASE_POWER = 45           # %
LIGHT_SETPOINT = 27             # %
Kp, Ki, Kd = 2.3, 0.00, 1.5            # PID constants
consts = [Kp, Ki, Kd]
co = 0
step = 0.1
zpomaleni = 1
btndelay = 100

# Acces global variable robot before using motors and sensors
global robot

# Initialize motors on ports M2 and M3
robot.init_motor(Port.M1)
robot.init_motor(Port.M2)

# Initialize Open-Cube RGB sensor on port S1
robot.init_sensor(sensor_type=Sensor.OC_COLOR, port=Port.S1)

# Regulator variables
e_sum = 0
e_prev = 0

# Follower regulation loop
while True:
    # Read light intensity
    light_intensity = robot.sensors.light[Port.S1].reflection() # 0-100%

    # TODO - PID regulator
    # 1. calculate error value e from light setpoint and measured ligth intensity
    e = LIGHT_SETPOINT-light_intensity

    # Exit program if left cube button is pressed
    buttons = robot.buttons.pressed()
    if buttons[Button.LEFT]:
        break
    if buttons[Button.RIGHT]:
        co += 1
        if co > 2:
            co = 0
        if(co == 0):
            step = 0.1
        elif(co == 1):
            step = 0.001
        else:
            step = 0.25
        time.sleep_ms(btndelay)
    if buttons[Button.UP]:
        consts[co] += step
        time.sleep_ms(btndelay)
    if buttons[Button.DOWN]:
        consts[co] -= step
        time.sleep_ms(btndelay)
    if buttons[Button.OK]:
        e_sum = 0
        e_prev = 0
        e = 0
        time.sleep_ms(btndelay)

    p = consts[0]*e
    i = consts[1]*e_sum
    d = consts[2]*(e-e_prev)
    # 2. calculate motor_pwr using error variables (e, e_sum, e_prev) and PID constants (Kp, Ki, Kd)
    motor_pwr = p + i + d

    # 3. save previous error for the derivative part
    e_prev = e

    # 4. Save sum of errors for the integral part
    e_sum += e

    # Set motor power
    pwr1 = (MOTOR_BASE_POWER + motor_pwr)/zpomaleni
    pwr2 = (MOTOR_BASE_POWER - motor_pwr)/zpomaleni
    robot.motors[Port.M1].set_power(pwr1)
    robot.motors[Port.M2].set_power(pwr2)

    robot.display.fill(0)
    a = "-"
    b = "-"
    c = "-"
    if(co == 0):
        a = "*"
    elif(co == 1):
        b = "*"
    elif(co == 2):
        c = "*"
    #robot.display.text(f"S1: {light_intensity}", 0, 0, 1)
    #robot.display.text(f"M1: {pwr1}", 0, 8, 1)
    #robot.display.text(f"M2: {pwr2}", 0, 16, 1)
    #robot.display.text(f"{a}P: {consts[0]}", 0, 24, 1)
    #robot.display.text(f"{b}I: {consts[1]}", 0, 32, 1)
    #robot.display.text(f"{c}D: {consts[2]}", 0, 40, 1)
    #robot.display.text("Reflection raw:", 0, 8, 1)
    #robot.display.show()
    
    # Do nothing
    time.sleep_ms(REGULATION_PERIOD_MS)



