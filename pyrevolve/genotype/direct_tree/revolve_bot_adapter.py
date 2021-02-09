from collections import OrderedDict

from pyrevolve.angle import Tree
from pyrevolve.revolve_bot import RevolveModule
from pyrevolve.revolve_bot.revolve_module import Orientation


def _get_orientation(orientation):
    if orientation == 0:
        return Orientation.FORWARD
    elif orientation == 1:
        return Orientation.RIGHT
    elif orientation == 2:
        return Orientation.BACK
    elif orientation == 3:
        return Orientation.LEFT


class RevolveBotAdapter:

    def __init__(self):
        self.id = 0

    def body_from_tree(self, tree: Tree):
        self.id = 0
        yaml = self._tree_to_yaml(tree.root)
        return RevolveModule().FromYaml(yaml)

    def _tree_to_yaml(self, node, orientation=0):
        yaml_dict_object = OrderedDict()
        yaml_dict_object['id'] = self.id
        yaml_dict_object['type'] = node.part.type
        yaml_dict_object['orientation'] = node.part.orientation
        self.id += 1

        children = self._generate_yaml_children(node)
        if children is not None:
            yaml_dict_object['children'] = children

        return yaml_dict_object

    def _generate_yaml_children(self, node):
        has_children = False

        children = {}
        for child_key in node.connections.keys():
            if node.connections[child_key].parent:
                next_node = node.connections[child_key].node
                children[child_key] = self._tree_to_yaml(next_node, child_key)
                has_children = True

        return children if has_children else None
