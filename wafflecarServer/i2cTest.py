import PCA9685
import time

pwm = PCA9685.PCA9685()

servo_min = 440 # 100
servo_mid = 480
servo_max = 520

def set_servo_pulse(channel, pulse):
	pulse_length = 1000000
	pulse *= 1000
	pwm.set_pwm(channel, 0, pulse)

pwm.set_pwm_freq(50)

angle = 130
# pwm.set_pwm(0, 0, 440)
# time.sleep(1)
# while True:
# 	pwm.set_pwm(0, 0, servo_min)
# 	time.sleep(1)
# 	pwm.set_pwm(0, 0, servo_mid)
# 	time.sleep(1)
# 	pwm.set_pwm(0, 0, servo_max)
# 	time.sleep(1)
# 	pwm.set_pwm(0, 0, servo_mid)
# 	time.sleep(1)
# 	break
	
# 	angle += 10
# 	pwm.set_pwm(0, 0, angle)
# 	print(angle)
# 	time.sleep(0.3)
# 	if angle > 650:
# 		break


# 1750, 2048 : very slow
# 1500, 2048 : slow
# 900, 2048 : normal
# 100, 2048 : fast
# 4096, 0 : very fast


pwm.set_pwm(3, 4096, 0)
pwm.set_pwm(2, 0, 4096)
# pwm.set_pwm(5, 0, 4096)
# pwm.set_pwm(4, 1024, 0)
time.sleep(2)
pwm.set_pwm(3, 0, 0)
pwm.set_pwm(4, 0, 0)

