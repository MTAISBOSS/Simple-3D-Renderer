from object_3d import *
from camera import *
from projection import *
import pygame as pg
import numpy as np

class SoftwareRender:
    def __init__(self):
        pg.init()
        self.RES = self.WIDTH, self.HEIGHT = 1600, 900
        self.H_WIDTH, self.H_HEIGHT = self.WIDTH // 2, self.HEIGHT // 2
        self.FPS = 60
        self.screen = pg.display.set_mode(self.RES)
        self.clock = pg.time.Clock()
        self.create_objects()
        
        self.selected_object = None
        self.dragging = False
        self.drag_offset = None
        self.mode = "VIEW"

    def create_objects(self):
        self.camera = Camera(self, [-5, 6, -55])
        self.projection = Projection(self)
        
        self.objects = []
        
        self.grid = Grid(self, size=20, spacing=1)
        self.grid.translate  = [0,-5,0]
        self.objects.append(self.grid)
        
        
        self.axes = AxesIndicator(self, position=[0, 0, 0], scale=2)
        self.objects.append(self.axes)
        
        self.model = self.get_object_from_file('model/object_3d.obj')
        self.model.rotate_y(-math.pi / 4)
        self.model.label = "My Lovely Stanford Bunny"
        self.model.scale_factor = 0.01
        self.objects.append(self.model)
        
        self.test_cube = Cube(self, position=[3, 2, 0], size=1)
        self.test_cube.label = "Cube"
        self.objects.append(self.test_cube)

    def get_object_from_file(self, filename):
        vertex, faces = [], []
        with open(filename) as f:
            for line in f:
                if line.startswith('v '):
                    vertex.append([float(i) for i in line.split()[1:]] + [1])
                elif line.startswith('f'):
                    faces_ = line.split()[1:]
                    faces.append([int(face_.split('/')[0]) - 1 for face_ in faces_])
        return Object3D(self, vertex, faces)

    def draw(self):
        self.screen.fill(pg.Color('black'))
        
        self.grid.draw()
        
        for obj in self.objects:
            if obj != self.grid:
                obj.draw()
        
        self.draw_ui()

    def draw_ui(self):
        font = pg.font.SysFont('Arial', 20)
        mode_text = font.render(f"Mode: {self.mode}", True, pg.Color('white'))
        self.screen.blit(mode_text, (10, 10))
        
        if self.selected_object and hasattr(self.selected_object, 'label'):
            selected_text = font.render(f"Selected: {self.selected_object.label}", True, pg.Color('yellow'))
            self.screen.blit(selected_text, (10, 40))
        
        instructions = [
            "WASD + QE: Move camera",
            "Arrow Keys: Rotate camera",
            "T: Translate mode",
            "R: Rotate mode",
            "S: Scale mode",
            "V: View mode",
            "Click: Select object",
            "Drag: Move/rotate/scale object",
            "Esc: Deselect"
        ]
        
        for i, text in enumerate(instructions):
            instr = font.render(text, True, pg.Color('lightgray'))
            self.screen.blit(instr, (self.WIDTH - 300, 10 + i * 25))

    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.selected_object = None
                elif event.key == pg.K_v:
                    self.mode = "VIEW"
                elif event.key == pg.K_t:
                    self.mode = "TRANSLATE"
                elif event.key == pg.K_r:
                    self.mode = "ROTATE"
                elif event.key == pg.K_s:
                    self.mode = "SCALE"
            
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_object_selection(event.pos)
            
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
                    self.drag_offset = None
            
            elif event.type == pg.MOUSEMOTION:
                if self.dragging and self.selected_object:
                    self.handle_object_drag(event.pos, event.rel)
        
        return True

    def handle_object_selection(self, mouse_pos):
        closest_obj = None
        closest_dist = float('inf')
        
        for obj in self.objects:
            if hasattr(obj, 'get_screen_center'):
                screen_center = obj.get_screen_center()
                if screen_center is not None:
                    dist = np.sqrt((screen_center[0] - mouse_pos[0])**2 + 
                                 (screen_center[1] - mouse_pos[1])**2)
                    
                    if dist < 50 and dist < closest_dist:
                        closest_dist = dist
                        closest_obj = obj
        
        self.selected_object = closest_obj
        if self.selected_object and self.mode != "VIEW":
            self.dragging = True
            self.drag_offset = mouse_pos

    def handle_object_drag(self, mouse_pos, rel):
        if not self.selected_object:
            return
        
        if self.mode == "TRANSLATE":
            sensitivity = 0.01
            dx = rel[0] * sensitivity
            dy = -rel[1] * sensitivity
            self.selected_object.translate([dx, dy, 0])
        
        elif self.mode == "ROTATE":
            sensitivity = 0.01
            self.selected_object.rotate_y(rel[0] * sensitivity)
            self.selected_object.rotate_x(rel[1] * sensitivity)
        
        elif self.mode == "SCALE":
            sensitivity = 0.01
            scale_factor = 1 + rel[1] * sensitivity
            self.selected_object.scale(scale_factor)

    def run(self):
        while True:
            if not self.handle_events():
                break
            
            self.draw()
            self.camera.control()
            
            for obj in self.objects:
                if hasattr(obj, 'update'):
                    obj.update()
            
            pg.display.set_caption(f"3D Renderer - FPS: {self.clock.get_fps():.1f}")
            pg.display.flip()
            self.clock.tick(self.FPS)

if __name__ == '__main__':
    app = SoftwareRender()
    app.run()