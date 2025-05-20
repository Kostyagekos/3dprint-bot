import trimesh

def render_model_screenshot(path_to_stl, output_path):
    mesh = trimesh.load_mesh(path_to_stl)
    scene = mesh.scene()
    png = scene.save_image(resolution=(600, 600), visible=True)
    with open(output_path, 'wb') as f:
        f.write(png)
