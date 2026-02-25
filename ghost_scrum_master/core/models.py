from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Commit:
    hash: str
    author: str
    date: str
    message: str
    diff: str

@dataclass
class Ticket:
    id: str
    title: str
    status: str
    assignee: str
    description: str

@dataclass
class ProjectState:
    tickets: List[Ticket]
    recent_commits: List[Commit]
