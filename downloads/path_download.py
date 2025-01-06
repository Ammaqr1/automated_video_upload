import os


def path_for_image_downloder_cwd():
    current_path = os.path.dirname(__file__)
    print(current_path)
    return current_path

