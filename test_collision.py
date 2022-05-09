from gemini import Scene, Entity, sleep, main_scene
import random

scene1 = Scene((20,15), is_main_scene=True)

floor = Entity((5,10), (10,1))

for _ in range(10):
	new_block = Entity((random.randint(4,14),0),(2,2), auto_render=True, collisions=True)
	direction = random.choice([1,-1])
	while True:
		is_collided = new_block.move(0,direction)
		if is_collided == 1:
			break
		sleep(.1)

scene2 = Scene((15,20), is_main_scene=True)
scene2.use_seperator = False

floor = Entity((4,5), (1,10))

for _ in range(10):
	new_block = Entity((12,random.randint(5,14)),(2,1), auto_render=True, collisions=True)
	direction = random.choice([1,-1])
	while True:
		is_collided = new_block.move(direction,0)
		if is_collided == 1:
			break
		sleep(.1)
