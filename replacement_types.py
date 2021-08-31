from typing import TypedDict, Union
from discord import File, Embed


class ReplacementType(TypedDict):
    '''Type for an Replacement'''
    lesson: str
    teacher: str
    subject: str
    replacing_teacher: str
    room: str
    info_text: str
    type_of_replacement: str


class MessageData(TypedDict):
    '''Syntax of a discord.Message'''
    files: list[File]
    embeds: list[Embed]


PlanPreview = Union[File, str]
