import math
from wafflecarUtil import *

import random

number = None
answer = None

def text_prompt(msg):
	try:
		return raw_input(msg)
	except NameError:
		return input(msg)


number = random.randint(1, 100)
while True:
	print('up')
	print(number)
	answer = int(input('input number: '))
	print(answer)
	break
