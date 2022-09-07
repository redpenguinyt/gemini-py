import os
from .utils import main_scene, txtcolours, printd, Vec2D, force_types, sleep
from .input import Input
from .camera import Camera
from . import utils

# -- Entities --

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
		if (self._parent != value or value is None) and self._parent:
			self._parent.children.remove(self)
		if value != None:
			value.add_to_scene(self)

	@property
	def fill_char(self):
		return self._fill_char if self.visible else self.parent.background_tile
	@fill_char.setter
	def fill_char(self, value: str):
		self._fill_char = value
	@property
	def pos(self):
		return Vec2D(self._pos)
	@pos.setter
	def pos(self, value: Vec2D):
		self._pos = Vec2D(value) % self.parent.size if self.parent else Vec2D(value)
	@pos.deleter
	def pos(self):
		del self._pos
	@property
	def all_positions(self):
		return [((self.pos + (i,j)) % self.parent.size) for i in range(self.size[0]) for j in range(self.size[1])]

	def __init__(self, pos: Vec2D, size: Vec2D, parent: 'Scene'=None, auto_render:bool=False, layer: int=0, fill_char:str="█", colour:str="", collisions: list[int]|bool=[], visible:bool=True, move_functions: list=[]):
		self._parent: 'Scene' = None
		if parent := parent or main_scene.main_scene:
			self.parent = parent

		self._pos = Vec2D(0,0)
		self.pos, self.size, self.fill_char = pos, Vec2D(size), fill_char
		self.colour, self.layer = colour, layer
		self.auto_render, self.visible = auto_render, visible
		self.collisions: list = [-1] if collisions == True else [] if collisions == False else collisions
		self.move_functions: list[function] = move_functions

	def __str__(self):
		return f"Entity(pos={self.pos},size={self.size},fill_char='{self._fill_char}')"

	def move(self, x:int|tuple, y:int=None, collide: bool=None, run_functions=True, render: bool=None):
		"""Move the Entity within the scene. `+x` is right and `+y` is down. By enabling the Entity's auto_render property, calling this function will automatically render the scene that this Entity belongs to. If your scene is stuttering while animating, make sure you're only rendering the scene once per frame.

		When collisions are on, the entity will collide with anything that isnt the background"""
		if render is None:
			render = self.auto_render

		has_collided = False

		move = Vec2D(x, y)

		if move.x != 0 or move.y != 0:
			if collide is None:
				collide = self.collisions
			if collide:
				prev_visible = self.visible
				self.visible = False

				bake = self.parent.render(False, self.collisions, False)

				def step_collide(axis: utils.Axis, p):
					if p == 0:
						return
					colliding = abs(p)
					polarity = (1 if p > 0 else -1)
					for j in range(colliding):
						for wall_p in range(self.size[0 if axis is utils.Axis.Y else 1]):
							next_pos = axis.vector( (self.size[axis.value] if p > 0 else -1) + j * polarity, wall_p )
							if self.parent.is_entity_at(self.pos + next_pos, self.collisions, bake):
								nonlocal has_collided
								colliding, has_collided = j, True

						if colliding < abs(p):
							break
					self.pos += axis.vector(colliding * polarity)

				step_collide(utils.Axis.X, move.x)
				step_collide(utils.Axis.Y, move.y)

				self.visible = prev_visible
			else:
				self.pos += move

			if run_functions and not has_collided:
				for func in self.move_functions:
					func()

		if render:
			self.parent.render()

		return 1 if has_collided else 0

	def get_pixel(self, pos: Vec2D) -> str:
		return self.fill_char

class Point(Entity):
	"""## Point
	An Instance of `Entity` with size (1,1). Helpful for temporary points in renders, simply add `gemini.Point.clear_points(scene)` to `scene.render_functions` (`scene` being your Scene instance)"""

	@property
	def all_positions(self):
		return [self.pos]

	def __init__(self, pos: Vec2D, fill_char: str = "█", parent: 'Scene' = None, layer: int = 0, colour: str = "",visible: bool = True,):
		super().__init__(pos, (1,1), parent, False, layer, fill_char, colour, [], visible, [])

	def __str__(self):
		return f"Point(pos={self.pos},fill_char='{self._fill_char}')"

class Line(Entity):
	"""## Line
	An object to handle automatic generation of lines. Accepts a `pos1` and a `pos2` variable. Inherits from `BaseEntity`. Lines are generated using Bresenham's line algorithm
	"""

	@property
	def pos0(self):
		return Vec2D(self._pos0)
	@pos0.setter
	def pos0(self, value: Vec2D):
		self._pos0 = Vec2D(value) % self.parent.size if self.parent else Vec2D(value)

	@property
	def pos1(self):
		return Vec2D(self._pos1)
	@pos1.setter
	def pos1(self, value: Vec2D):
		self._pos1 = Vec2D(value) % self.parent.size if self.parent else Vec2D(value)

	@property
	def all_positions(self):
		x0, y0 = self.pos0
		x1, y1 = self.pos1
		positions = []
		dx = abs(x1 - x0)
		sx = 1 if x0 < x1 else -1
		dy = -abs(y1 - y0)
		sy = 1 if y0 < y1 else -1
		error = dx + dy

		while True:
			positions.append(Vec2D(x0, y0))
			e2 = error * 2
			if e2 >= dy:
				if x0 == x1: break
				error += dy
				x0 += sx
			if e2 <= dx:
				if y0 == y1: break
				error += dx
				y0 += sy

		return positions

	def __init__(self, pos0: Vec2D, pos1: Vec2D, parent: 'Scene' = None, layer: int = 0, fill_char: str = "█", colour: str = "", visible: bool = True):
		super().__init__((0,0), (0,0), parent, False, layer, fill_char, colour, [], visible, None)
		self.pos0 = pos0
		self.pos1 = pos1

	def __str__(self):
		return f"Line(pos0={self.pos0},pos1={self.pos1},fill_char='{self._fill_char}')"

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

	In the event that a single character takes up two spaces (e.g. ¯\_(ツ)_/¯), you can use the `extra_characters` parameter, with each index of the list corresponding to the line with the extra character. For instance with a sprite with the image `¯\_(ツ)_/¯`, you would set `extra_characters=[1]`
	"""

	@property
	def image(self):
		"""This will return nothing if the sprite is hidden, to always get the raw image"""
		return self._image if self.visible else " \n"*self.size[1]
	@image.setter
	def image(self, value: str):
		self._image = value
		self.size = Vec2D(len(max(value.split("\n"), key= lambda x: len(x))), value.count("\n") + 1)

	@property
	def render_image(self):
		"""Regular image but with the extra characters"""
		render_image = self.image.split("\n")
		for i, n in enumerate(self.extra_characters):
			render_image[i] += "​"*n # Add zero width spaces
		return '\n'.join(render_image)
	@property
	def all_positions(self):
		raw_positions = []
		for j in range(self.size[1]):
			length = self.size[0] + (
				self.extra_characters[j] if len(self.extra_characters) > j else 0
			)
			raw_positions.extend([(i,j) for i in range(length)])
		return [
			(self.pos + pos) % self.parent.size for pos in raw_positions
			if self.get_pixel(pos) != " " or not self.transparent
		]

	def __init__(self, pos: Vec2D, image: str, transparent: bool=True, extra_characters: list=[], *args, **kwargs):
		super().__init__(pos, (0,0), *args, **kwargs) # dummy size parameter
		self.transparent = transparent
		self.extra_characters = extra_characters
		self.image = image.strip("\n")
		del self._fill_char

	def __str__(self):
		return f"Sprite(pos={self.pos},image='{self._image[:10]}{'...' if len(self._image) > 10 else ''}')"

	def get_pixel(self, pos: Vec2D) -> str:
		try:
			return self.render_image.split("\n")[pos[1]][pos[0]]
		except Exception:
			return " "

class AnimatedSprite(Sprite):
	"""## AnimatedSprite
	The AnimatedSpite object works the same way as the Sprite class, but accepts a list of images instead of only one, and can be set which to show with the `current_frame` value. The `image` property will now return the current frame as an image

	This here will create an AnimatedSprite PacMan whose mouth will change every time the move function is used:
	>>> from gemini import Scene, AnimatedSprite
	scene = Scene((10,10))
	new_entity = AnimatedSprite((5,5), ["O","C","<","C"], parent)
	new_entities.move_functions.append(new_entity.next_frame,)
	```"""

	@property
	def current_frame(self):
		"""Returns the index of the current frame, to get a picture of the actual frame use self.image.
		When setting the current_frame, the index will always autocorrect itself to be within the fram list's range."""
		return self._current_frame
	@current_frame.setter
	def current_frame(self, value: int):
		self._current_frame = value % len(self.frames)
		self.image = self.frames[self._current_frame]

	def __init__(self, pos: Vec2D, frames: list, *args, **kwargs):
		self.frames = [frame.strip("\n") for frame in frames]
		self._current_frame = 0

		super().__init__(pos, frames[0], *args, **kwargs)

	def __str__(self):
		return f"AnimatedSprite(pos={self.pos},frames='{str(self.frames)[:20]}')"

	def next_frame(self):
		self.current_frame += 1

# -- Scene --

class Scene:
	"""## Scene
	You can attach entities to this scene and render the scene to display them. There can be more than one scene that can be rendered one after the other. Create a scene like so:
	>>> from gemini import Scene
	>>> new_scene = Scene((30,15))

	The width and height parameters are required and define the size of the rendered scene. To set the scene size to be the current terminal size, by using `os.get_terminal_size()`

	Using is_main_scene=True is the same as
	>>> from gemini import Scene, set_main_scene
	>>> new_scene = Scene((10,10))
	>>> set_main_scene(new_scene)

	The `render_functions` parameter is to be a list of functions to run before any render, except when the `run_functions` parameter is set to False"""
	use_separator = True
	_void_char = '¶'

	@property
	def is_main_scene(self):
		return main_scene.main_scene == self
	@is_main_scene.setter
	def is_main_scene(self, value):
		main_scene.main_scene = self if value else None

	@property
	def background_tile(self):
		"""Return the background character with colours included"""
		return f"{self.bg_colour}{self.clear_char}{txtcolours.END if self.bg_colour != '' else ''}"

	def __init__(self, size: Vec2D, clear_char="░", bg_colour="", children: list[Entity]=[], render_functions: list=[], is_main_scene=False):
		self.size = Vec2D(size)
		self.clear_char = clear_char
		self.bg_colour = bg_colour
		self.children: list[Entity] = []
		self.render_functions: list[function] = render_functions

		if is_main_scene:
			self.is_main_scene = True

		for child in children[:]:
			self.add_to_scene(child)

	def __str__(self):
		return f"Scene(size={self.size},clear_char='{self.clear_char}',is_main_scene={self.is_main_scene})"

	def add_to_scene(self, new_entity: Entity):
		"""Add an entity to the scene. This can be used instead of directly defining the entity's parent, or if you want to move the entity between different scenes"""
		self.children.append(new_entity)
		new_entity._parent = self

	def clear_points(self):
		"""Remove all `Point` objects"""
		for point in filter(lambda x: isinstance(x, Point), self.children[:]):
			point.parent = None

	def get_separator(self, use_separator=None, used_lines=None):
		"""Create a use_separator to put above display so that you can only see one rendered scene at a time"""
		if use_separator is None:
			use_separator = self.use_separator

		seperator = "\n" * (os.get_terminal_size().lines - (used_lines or self.size[1]))

		return seperator if use_separator else ""

	def _render_stage(self, stage: list[list], show_coord_numbers=False, starting_coords=(0,0)):
		"""Return a baked scene, ready for printing. This will take your grid of strings and render it. You can also set `show_coord_numbers=True` to print your scene with coordinate numbers for debugging purposes"""
		if show_coord_numbers:
			for i, c in enumerate(stage, starting_coords[1]):
				c.insert(0, str(i)[-1:])
			stage.insert( 0, [' '] + [ str(starting_coords[0]+i)[-1:] for i in range(len(stage[0])-1) ] )
		return "\n".join(["".join(row) for row in stage])+"\n"

	def render(self, is_display=True, layers: list=None, run_functions=True, *, _output=True, show_coord_numbers=False, use_separator=None):
		"""This will print out all the entities that are part of the scene with their current settings. The character `¶` can be used as a whitespace in Sprites, as regular ` ` characters are considered transparent, unless the transparent parameter is disabled, in which case all whitespaces are rendered over the background.

		When rendering an animation, make sure to put a short pause in between frames to set your fps. `gemini.sleep(0.1)` will mean a new fram every 0.1 seconds, aka 10 FPS

		If your scene is stuttering while animating, make sure you're only rendering the scene once per frame

		If the `layers` parameter is set, only entities on those layers will be rendered. Entities will also be rendered in the order of layers, with the smallest layer first

		For debugging, you can set `show_coord_numbers=True` to more see coordinate numbers around the border of your rendered scene. These numbers will not show in the render function's raw output regardless
		"""

		stage = [[self.background_tile] * self.size[0] for _ in range(self.size[1])] # Create the render 'stage'
		entity_list = list(filter(lambda x: x.layer in layers, self.children)) if layers and layers != [-1] else self.children # Get a list of the entities the user wants to render
		for entity in sorted(entity_list, key=lambda x: x.layer, reverse=True):
			# Add each pixel of an entity to the stage
			for position in entity.all_positions:
				pixel = entity.get_pixel(
					(position - entity.pos) % self.size
				).replace(self._void_char,' ')
				stage[position[1]][position[0]] = f"{entity.colour}{pixel}{txtcolours.END if entity.colour else ''}"

		if run_functions:
			for function in self.render_functions:
				function()

		if is_display:
			self.clear_points()
			print(
				self.get_separator(use_separator) +
				self._render_stage(stage, show_coord_numbers)
			)
		if _output:
			return stage

	def is_entity_at(self, pos: Vec2D, layers: list=[-1], bake=None):
		"""Check for any object at a specific position, can be sorted by layers. `-1` in the layers list means to collide with all layers"""
		layers = layers if isinstance(layers, list) else [layers]
		render = bake or self.render(is_display=False, layers=None if -1 in layers else layers, run_functions=False)
		pos = Vec2D(pos) % self.size
		coordinate = render[pos[1]][pos[0]]
		return coordinate != self.background_tile

	def get_entities_at(self, pos: Vec2D, layers: list[int]=[]) -> list[Entity]:
		"""Return all entities found at the chosen position, can be filtered by layer"""
		layers = layers if isinstance(layers, list) else [layers]
		layers = layers if layers != [-1] else []
		entities: list[Entity] = list(filter(lambda x: x.layer in layers, self.children)) if layers else self.children

		return list(filter(lambda x: pos in x.all_positions, entities))
