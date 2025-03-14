from project.project import Project
from singleton import singleton
from utils.ui_property import UiProperty


@singleton
class RuntimeVars:
    def __init__(self) -> None:
        self.project: Project = Project()
        self.page: UiProperty[int] = UiProperty(0)
