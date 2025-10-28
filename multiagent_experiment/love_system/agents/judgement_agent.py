from .base_agent import BaseAgent
from ..tools import judgement_tools


class JudgementAgent(BaseAgent):
    def __init__(self):
        super().__init__("JudgementAgent")

    def check_all_true(self, conditions: list) -> bool:
        return judgement_tools.check_all_true(conditions)

    def is_towards(self, feeling: object, target: object) -> bool:
        return judgement_tools.is_towards(feeling, target)

    def shows_through(self, feeling: object, actions: list) -> bool:
        return judgement_tools.shows_through(feeling, actions)

    def exists_between(self, feeling: object, entities: list) -> bool:
        return judgement_tools.exists_between(feeling, entities)

    def is_accepting_and_wants_happiness(self, someone: object, feeling: object) -> bool:
        return judgement_tools.is_accepting_and_wants_happiness(someone, feeling)

    def has_dual_nature(self, feeling: object, emotion: object, decision: object) -> bool:
        return judgement_tools.has_dual_nature(feeling, emotion, decision)

    def is_wanting_wellbeing(self, emotion: object, someone: object) -> bool:
        return judgement_tools.is_wanting_wellbeing(emotion, someone)

    def is_putting_wellbeing_first(self, decision: object, someone: object) -> bool:
        return judgement_tools.is_putting_wellbeing_first(decision, someone)
