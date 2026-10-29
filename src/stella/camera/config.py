import gphoto2 as gp

class CameraConfig:
    def __init__(self, manager):
        self.manager = manager

    def get_config_tree(self):
        camera = self.manager.get_camera()
        return camera.get_config(self.manager.context)

    def set_config_tree(self, config_tree):
        camera = self.manager.get_camera()
        camera.set_config(config_tree, self.manager.context)

    def get_parameter(self, param_name):
        config_tree = self.get_config_tree()
        child = config_tree.get_child_by_name(param_name)
        return child.get_value()

    def set_parameter(self, param_name, value):
        config_tree = self.get_config_tree()
        child = config_tree.get_child_by_name(param_name)
        child.set_value(value)
        self.set_config_tree(config_tree)

    def list_all_parameters(self):
        config_tree = self.get_config_tree()
        params = {}
        
        def traverse(node):
            if node.count_children() > 0:
                for i in range(node.count_children()):
                    traverse(node.get_child(i))
            else:
                params[node.get_name()] = node.get_value()
                
        traverse(config_tree)
        return params
