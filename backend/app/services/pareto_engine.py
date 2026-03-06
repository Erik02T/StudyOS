from app.models.subject import Subject
from app.models.task import Task


class ParetoEngine:
    @staticmethod
    def priority_score(subject: Subject, task: Task) -> float:
        importance = max(subject.importance_level, 1)
        usage_frequency = max(100 - task.mastery_level, 1)
        difficulty = max(subject.difficulty, 1)
        return round((importance * usage_frequency) / difficulty, 2)

