# state.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MatchData:
    match_number: int
    contestant1_id: int       # Discord user ID
    contestant2_id: int
    judge_id: int
    stadium: int
    challonge_match_id: int
    started: bool = False

@dataclass 
class TournamentState:
    active: bool = False
    name: str = ""
    challonge_tournament_id: str = ""
    stadium_count: int = 0
    battle_start_time: int = 0        # minutes
    
    participants: dict = field(default_factory=dict)
    
    # Discord user IDs
    contestants_available: list = field(default_factory=list)
    contestants_busy: list = field(default_factory=list)
    judges_available: list = field(default_factory=list)
    judges_busy: list = field(default_factory=list)
    
    # Matches — keyed by match number
    matches: dict = field(default_factory=dict)
    match_counter: int = 0
    
    # stadiums — which are in use
    stadiums_in_use: list = field(default_factory=list)

# Single global instance — imported everywhere
tournament = TournamentState()