from gemini import Scene, Entity

scene1 = Scene((15,10))
scene2 = Scene((10,12))
scene2.use_seperator = False

entity1 = Entity((5,5), (2,1), parent=scene1)
entity1 = Entity((5,10), (4,2), parent=scene2)

scene1.render()
scene2.render()