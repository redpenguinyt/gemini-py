import os
from time import sleep
from .utils import correct_position, main_scene, txtcolours, printd
from .input import Input

# main engine file

main_scene = main_scene

class Entity:
	"""## Entity
	The Entity is the most basic object in a Gemini Scene. It is simply a rectangle of your chosen proportions. You can create a new entity like so.

	>>> from gemini import Scene, Entity
	>>> new_scene = Scene((30,15))
	>>> new_entity = Entity(pos=(5,4), size=(2,1), parent=new_scene)

	You can also set all entities created to have the same parent like this:
	>>> new_scene = Scene((30,15), is_main_scene=True)
	>>> new_entity = Entity((5,4), (2,1))
	"""
	@property
	def parent(self):
		return self._parent

	@parent.setter
	def parent(self, value: 'Scene'):
		if value == None:
			self._parent.children.remove(self)
		self._parent = value

	def __init__(self, pos: tuple, size: tuple, parent: 'Scene'=None, auto_render=False, layer=0, fill_char="█", colour="", collisions: list|bool=[]):
		self.pos, self.size = pos, size
		self.fill_char = fill_char
		self.old_fill_char = self.fill_char
		self.colour = colour
		self.auto_render = auto_render
		self.layer = layer
		self.collisions = [-1] if collisions == True else [] if type(collisions) == bool else collisions

		if not parent and main_scene.main_scene:
			parent = main_scene.main_scene
		self._parent = parent
		if parent:
			parent.add_to_scene(self)

	def move(self, x: int | tuple, y: int=None, collide: bool=None, render: bool=None):
		"""Move the Entity within the scene. `+x` is right and `+y` is down. By enabling the Entity's auto_render property, calling this function will automatically render the scene that this Entity belongs to. If your scene is stuttering while animating, make sure you're only rendering the scene once per frame.

		When collisions are on, the entity will collide with anything that isnt the background"""
		if collide == None:
			collide = len(self.collisions) > 0
		if render == None:
			render = self.auto_render

		has_collided = False

		y = y if type(x) == int else x[1]
		x = x if type(x) == int else x[0]

		self.hide()

		if collide:
			for _ in range(abs(x)):
				colliding = False
				for wall_y in range(self.size[1]):
					if self.parent.is_entity_at((self.pos[0] + (self.size[0] if x > 0 else -1), self.pos[1] + wall_y), layers=self.collisions):
						colliding, has_collided = True, True
				if colliding:
					break
				else:
					self.move(1 if x > 0 else -1, 0, collide=False, render=False)
			for _ in range(abs(y)):
				colliding = False
				for wall_x in range(self.size[0]):
					if self.parent.is_entity_at((self.pos[0] + wall_x, self.pos[1] + (self.size[1] if y > 0 else -1)), layers=self.collisions):
						colliding, has_collided = True, True
				if colliding:
					break
				else:
					self.move(0,1 if y > 0 else -1, collide=False, render=False)
		else:
			self.pos = tuple(correct_position((self.pos[0] + x, self.pos[1] + y), self.parent.size))

		self.show()

		if render:
			self.parent.render()

		return 1 if has_collided else 0

	def show(self):
		self.fill_char = self.old_fill_char
	def hide(self):
		self.fill_char = self.parent.get_background()

class Sprite(Entity):
	"""## Sprite
	An entity with a give ASCII art that is rendered on the Scene, this can be used to put text on the scene, like so:
	>>> from gemini import Scene, Sprite
	>>> scene = Scene((13,3))
	>>> text = Sprite((1,1), image="Hello there", parent=scene, transparent=False)
	>>> scene.render()
	░░░░░░░░░░░░░
	░Hello there░
	░░░░░░░░░░░░░

	This makes it easy to put existing ascii art into whatever you're making, and move it around!

	In the event that a single character takes up two spaces (e.g. ¯\_(ツ)_/¯), you can use the extra_characters parameter, with each index of the list corresponding to the line with the extra character. For instance with a sprite with the image `¯\_(ツ)_/¯`, you would set `extra_characters=[1]`
	"""

	def __init__(self, pos: tuple, image: str, transparent: bool=True, parent: 'Scene'=None, auto_render=False, layer=0, colour: str="", collisions: list=[], extra_characters: list=[]):
		self.old_image = image
		self.image = image
		self.transparent = transparent
		self.extra_characters = extra_characters

		size = (len(max(image.split("\n"))), image.count("\n") + 1)

		super().__init__(pos, size, parent, auto_render, layer, "", colour, collisions)
		del self.fill_char
		del self.old_fill_char

	def __str__(self):
		return f"Scene(size={self.size},clear_char='{self.clear_char}',bg_colour='{self.bg_colour}',is_main_scene={self == main_scene.main_scene})"

	def show(self):
		self.image = self.old_image

	def hide(self):
		self.image = " \n"*self.size[1]

class Scene:
	"""## Scene
	You can attach entities to this scene and render the scene to display them. There can be more than one scene that can be rendered one after the other. Create a scene like so:
	>>> from gemini import Scene
	>>> new_scene = Scene((30,15))

	The width and height parameters are required and define the size of the rendered scene. To set the scene size to be the current terminal size, by using `os.get_terminal_size()`

	Using is_main_scene=True is the same as
	>>> from gemini import Scene, set_main_scene
	>>> new_scene = Scene((10,10))
	>>> set_main_scene(new_scene)"""
	use_seperator = True

	def __init__(self, size: tuple, clear_char="░", bg_colour="", is_main_scene=False):
		self.size = size
		self.clear_char = clear_char
		self.bg_colour = bg_colour
		self.children = []

		if is_main_scene:
			main_scene.main_scene = self

	def __str__(self):
		return f"Scene(size={self.size},clear_char='{self.clear_char}',bg_colour='{self.bg_colour}',is_main_scene={self == main_scene.main_scene})"

	def add_to_scene(self, new_entity: Entity):
		"""Add an entity to the scene. This can be used instead of directly defining the entity's parent, or if you want to move the entity between different scenes"""
		self.children.append(new_entity)
		new_entity.parent = self

	def render(self, is_display=True, layers: list=None, _output=True):
		"""This will print out all the entities that are part of the scene with their current settings. The character `¶` can be used as a whitespace in Sprites, as regular ` ` characters are considered transparent, unless the transparent parameter is disabled, in which case all whitespaces are rendered over the background.

		When rendering an animation, make sure to use `time.sleep()` in between frames to set your fps. `time.sleep(0.1)` will mean a new fram every 0.1 seconds, aka 10 FPS

		If your scene is stuttering while animating, make sure you're only rendering the scene once per frame

		If the `layers` parameter is set, only objects on those layers will be rendered.
		"""
		seperator = "\n" * (os.get_terminal_size().lines - self.size[1]) if self.use_seperator else ""
		display = [[self.get_background()] * self.size[0] for _ in range(self.size[1])]

		entity_list = list(filter(lambda x: x.layer in layers, self.children)) if layers else self.children
		for entity in sorted(entity_list, key=lambda x: x.layer, reverse=True):
			extra_length = 0
			if isinstance(entity, Sprite):
				entity_image = entity.image.split("\n")
				for i, n in enumerate(entity.extra_characters):
					print(f"yooo: {i}, {n}")
					entity_image[i] += "​"*n # Add zero width spaces
				entity_image = '\n'.join(entity_image)
				print(entity_image)
				extra_length = max(entity.extra_characters)
			for x in range(entity.size[0]+extra_length):
				for y in range(entity.size[1]):
					if isinstance(entity, Sprite):
						try:
							print(__import__('json').dumps(entity_image))
							pixel = entity_image.split("\n")[y][x]
						except:
							pixel = " "
						if pixel == " " and entity.transparent:
							continue
					elif isinstance(entity, Entity):
						pixel = entity.fill_char

					point = [entity.pos[0]+x, entity.pos[1]+y]
					point = correct_position(point, self.size)
					display[point[1]][point[0]] = f"{entity.colour}{pixel.replace('¶',' ')}{txtcolours.END if entity.colour else ''}"

		if is_display:
			print(seperator+"\n".join(["".join(row) for row in display])+"\n")
		if _output:
			return display

	def get_background(self):
		"""Return the background character with colours included"""
		return f"{self.bg_colour}{self.clear_char}{txtcolours.END if self.bg_colour != '' else ''}"

	def is_entity_at(self, pos: tuple, layers: list=[-1]):
		"""Check for any object at a specific position, can be sorted by layers. `-1` in the layers list means to collide with all layers"""
		render = self.render(is_display=False, layers=None if -1 in layers else layers)
		pos = correct_position(pos, self.size)
		coordinate = render[pos[1]][pos[0]]
		if coordinate != self.get_background():
			return True

if __name__ == "__main__":
	print("This is the module file, please use a provided example instead")