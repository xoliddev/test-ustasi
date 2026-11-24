"""The service the bot, the Mini App API and the scheduler share: one set of rules, scoped by teacher and student."""

from __future__ import annotations

from .base import Base
from .drafts import Drafts
from .groups import Groups
from .publish import Publish
from .results import Results
from .seed import Seed
from .solving import Solving


class Service(Groups, Drafts, Publish, Solving, Results, Seed, Base):
    pass
