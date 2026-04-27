from kulms_download.shared.components import Resource


def show_tree_structure(root: Resource):
    if root is None:
        return ""

    lines = [str(root.title)]

    def recursive(node: Resource, prefix: str):
        child_count = len(node.children)
        for i, child in enumerate(node.children):
            is_last = i == child_count - 1
            branch = "`-- " if is_last else "|-- "
            lines.append(f"{prefix}{branch}{child.title}")
            next_prefix = f"{prefix}{'    ' if is_last else '|   '}"
            recursive(child, next_prefix)

    recursive(root, "")
    tree_text = "\n".join(lines)
    print(tree_text)
