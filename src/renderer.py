import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

def render_model_screenshot(path_to_stl, output_path):
    mesh = trimesh.load_mesh(path_to_stl)
    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(111, projection='3d')

    # Получаем вершины и грани
    vertices = mesh.vertices
    faces = mesh.faces
    mesh_collection = Poly3DCollection(vertices[faces], alpha=0.7)
    mesh_collection.set_edgecolor('k')
    ax.add_collection3d(mesh_collection)

    # Автоматическое масштабирование
    scale = vertices.flatten()
    ax.auto_scale_xyz(scale, scale, scale)

    # Без осей
    ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
