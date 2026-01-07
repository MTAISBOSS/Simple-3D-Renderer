import pygame as pg
from matrix_functions import *
from numba import njit
import numpy as np

@njit(fastmath=True)
def any_func(arr, a, b):
    return np.any((arr == a) | (arr == b))

class Object3D:
    def __init__(self, render, vertices='', faces='', position=None):
        self.render = render
        self.vertices = np.array(vertices, dtype=np.float64)
        self.faces = faces
        self.position = np.array(position if position else [0.0, 0.0, 0.0], dtype=np.float64)
        self.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.scale_factor = 1.0
        
        self.original_vertices = self.vertices.copy() if len(self.vertices) > 0 else None
        
        if len(self.vertices) > 0:
            self.update()

        self.font = pg.font.SysFont('Arial', 30, bold=True)
        self.color_faces = [(pg.Color('orange'), face) for face in self.faces]
        self.movement_flag, self.draw_vertices = False, False
        self.label = ''

    def draw(self):
        self.screen_projection()
        if self.movement_flag:
            self.rotate_y(-(pg.time.get_ticks() % 0.005))

    def screen_projection(self):
        if len(self.vertices) == 0:
            return
            
        vertices = self.vertices @ self.render.camera.camera_matrix()
        vertices = vertices @ self.render.projection.projection_matrix
        vertices /= vertices[:, -1].reshape(-1, 1)
        vertices[(vertices > 2) | (vertices < -2)] = 0
        vertices = vertices @ self.render.projection.to_screen_matrix
        vertices = vertices[:, :2]

        for index, color_face in enumerate(self.color_faces):
            color, face = color_face
            
            if self.render.selected_object == self:
                color = pg.Color('yellow') if index % 2 == 0 else pg.Color('gold')
                thickness = 3
            else:
                thickness = 1
                
            polygon = vertices[face]
            if not any_func(polygon, self.render.H_WIDTH, self.render.H_HEIGHT):
                pg.draw.polygon(self.render.screen, color, polygon, thickness)
                
                if self.label and index == 0:
                    text = self.font.render(self.label, True, pg.Color('white'))
                    text_rect = text.get_rect(center=polygon.mean(axis=0))
                    self.render.screen.blit(text, text_rect)

        if self.draw_vertices:
            for vertex in vertices:
                if not any_func(vertex, self.render.H_WIDTH, self.render.H_HEIGHT):
                    pg.draw.circle(self.render.screen, pg.Color('white'), vertex, 3)

    def get_screen_center(self):
        if len(self.vertices) == 0:
            return None
            
        vertices = self.vertices @ self.render.camera.camera_matrix()
        vertices = vertices @ self.render.projection.projection_matrix
        vertices /= vertices[:, -1].reshape(-1, 1)
        vertices = vertices @ self.render.projection.to_screen_matrix
        vertices = vertices[:, :2]
        
        return vertices.mean(axis=0)

    def update(self):
        if self.original_vertices is not None and len(self.original_vertices) > 0:
            self.vertices = self.original_vertices.copy()
            
            if self.scale_factor != 1.0:
                self.vertices = self.vertices @ scale(self.scale_factor)
            
            if np.any(self.rotation != 0):
                self.vertices = self.vertices @ rotate_x(self.rotation[0])
                self.vertices = self.vertices @ rotate_y(self.rotation[1])
                self.vertices = self.vertices @ rotate_z(self.rotation[2])
            
            self.vertices = self.vertices @ translate(self.position)

    def translate(self, pos):
        self.position = self.position + np.array(pos, dtype=np.float64)
        self.update()

    def set_position(self, pos):
        self.position = np.array(pos, dtype=np.float64)
        self.update()

    def rotate_x(self, angle):
        self.rotation[0] += angle
        self.update()

    def rotate_y(self, angle):
        self.rotation[1] += angle
        self.update()

    def rotate_z(self, angle):
        self.rotation[2] += angle
        self.update()

    def set_rotation(self, rot):
        self.rotation = np.array(rot, dtype=np.float64)
        self.update()

    def scale(self, scale_to):
        self.scale_factor *= scale_to
        self.update()

    def set_scale(self, scale_to):
        self.scale_factor = scale_to
        self.update()

class Grid(Object3D):
    def __init__(self, render, size=10, spacing=1):
        vertices = []
        faces = []
        
        for i in range(-size, size + 1, spacing):
            vertices.append([-size, 0.0, i, 1.0])
            vertices.append([size, 0.0, i, 1.0])
            faces.append([len(vertices)-2, len(vertices)-1])
            
            vertices.append([i, 0.0, -size, 1.0])
            vertices.append([i, 0.0, size, 1.0])
            faces.append([len(vertices)-2, len(vertices)-1])
        
        super().__init__(render, vertices, faces)
        self.movement_flag = False
        self.draw_vertices = False
        self.label = "Grid"
        
        self.color_faces = [(pg.Color('gray'), face) for face in self.faces]

class AxesIndicator(Object3D):
    def __init__(self, render, position=None, scale=1.0):
        vertices = [
            [0.0, 0.0, 0.0, 1.0],
            [scale, 0.0, 0.0, 1.0],
            [0.0, scale, 0.0, 1.0],
            [0.0, 0.0, scale, 1.0]
        ]
        
        faces = [
            [0, 1],
            [0, 2],
            [0, 3]
        ]
        
        super().__init__(render, vertices, faces, position)
        
        self.colors = [pg.Color('red'), pg.Color('green'), pg.Color('blue')]
        self.color_faces = [(color, face) for color, face in zip(self.colors, self.faces)]
        self.movement_flag = False
        self.draw_vertices = True
        self.label = "Axes"

class Cube(Object3D):
    def __init__(self, render, position=None, size=1.0):
        half = size / 2
        vertices = [
            [-half, -half, -half, 1.0],
            [half, -half, -half, 1.0],
            [half, half, -half, 1.0],
            [-half, half, -half, 1.0],
            [-half, -half, half, 1.0],
            [half, -half, half, 1.0],
            [half, half, half, 1.0],
            [-half, half, half, 1.0]
        ]
        
        faces = [
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [0, 1, 5, 4],
            [2, 3, 7, 6],
            [0, 3, 7, 4],
            [1, 2, 6, 5]
        ]
        
        super().__init__(render, vertices, faces, position)
        self.movement_flag = True
        self.draw_vertices = False