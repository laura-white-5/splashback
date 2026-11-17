""" Identity & Access module

Responsibility: who the user is and what they are allowed to see.
Prototype label: MOCKED - one hard-coded demo teacher, no login.
The interface (can_view) is the same one the real login system would provide.
"""

DEMO_TEACHER = {"user_id": "T1", "name": "Sarah K.", "role": "teacher"}


class AccessService:
    # Interface: can_view(user_id, child_id) -> bool

    def __init__(self, roster_service):
        self._roster = roster_service

    def current_user(self):
        # Mocked: always the demo teacher. A real version would let the user login
        return DEMO_TEACHER

    def can_view(self, user_id, child_id):
        # A teacher can view a child only if the child is in one of their classes
        for swim_class in self._roster.get_classes_for_teacher(user_id):
            if any(child.child_id == child_id for child in swim_class.children):
                return True
        return False