from util.log import Log
from pydantic import Field, BaseModel
from util.versionstamp import versionid, versionstamp
from typing import List, Optional, Dict, Any
vm = versionstamp()


class Lab:
    """
    id: versionid = Field(default_factory=vm)
    labname: str = Field(..., description="Name of the lab")
    labcode: str = Field(..., description="Unique code for the lab")
    location: str = Field(..., description="Location of the lab")
    projects: List['Project'] = Field(default_factory=list, description="List of projects in the lab")
    """

    def __init__(self, name: str, code: str, location: str, projects: Optional[List['Project']] = None):
        self.name = name
        self.code = code
        self.location = location
        self.projects = projects or []
        self.log = Log(name).with_context(
            lab_name=name,
            lab_code=code,
            location=location
        )
        self.id = vm()

    def create_project(self, project_name: str, description: Optional[str] = None, tags: Optional[List[str]] = None) -> 'Project':
        new_project = Project(
            name=project_name,
            description=description,
            tags=tags or [],
            lab_id=self.id
            )
        self.projects.append(new_project)
        return new_project

    def get_project_id(self, project_name: str) -> Optional[versionid]:
        for project in self.projects:
            if project.name == project_name:
                return project.id
        return None


class Project:
    """
    id: versionid = Field(default_factory=vm)
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    lab_id: versionid = Field(..., description="ID of the lab this project belongs to")
    """

    def __init__(self, name: str, lab_id:versionid,  description: Optional[str] = None, tags: Optional[List[str]] = None):
        self.name = name
        self.description = description or ""
        self.tags = tags or []
        self.lab_id = lab_id
        self.id = vm()
        self.log = Log(name).with_context(
            project_name=name,
            project_id=self.id,
            lab_id=lab_id
        )
        self.log.info(f"Project {self.name} created in lab {self.lab_id}")



# Manages and Executes experiments in the lab
class Execution:
    pass

