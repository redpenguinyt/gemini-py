from gemini import Scene, Entity, Sprite, txtcolours as tc, sleep

test_image = """  ______
 /|_||_\`.__
(¶¶¶_¶¶¶¶_¶_\\
=`-(_)--(_)-'"""

scene = Scene((30,10), bg_colour=tc.CYAN, is_main_scene=True)
car = Sprite((5,5), test_image, colour=tc.GREEN)
cloud = Entity((10,4), (4,2), fill_char="0", layer=-1)

cloud.hide()

while True:
	scene.render()
	car.move(1,0)
	cloud.show()
	cloud.move(-1,-1)
	sleep(.1)