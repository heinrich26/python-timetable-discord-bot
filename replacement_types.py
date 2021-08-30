from typing import TypedDict, Union
from discord import File

class ReplacementType(TypedDict):
    lesson: str
    teacher: str
    subject: str
    replacing_teacher: str
    room: str
    info_text: str
    type_of_replacement: str

PlanPreview = Union[File, str]
