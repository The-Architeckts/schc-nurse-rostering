'''
Data models for Nurse Rostering Problem.
Represents nurses, contracts, shift types, etc.
'''

class ShiftType:
    '''Binary encoding for shifts'''
    DH = 32    # 0b100000 - Day Head/Holiday (NEW)
    E = 16     # 0b010000 - Early
    L = 8      # 0b001000 - Late
    D = 4      # 0b000100 - Day
    N = 2      # 0b000010 - Night
    OFF = 1    # 0b000001 - Day off
    
    @staticmethod
    def from_string(shift_str):
        '''Convert shift string to binary'''
        mapping = {
            'DH': ShiftType.DH,  # NEW
            'E': ShiftType.E, 
            'L': ShiftType.L, 
            'D': ShiftType.D, 
            'N': ShiftType.N
        }
        return mapping.get(shift_str, ShiftType.OFF)
    
    @staticmethod
    def to_string(shift_int):
        '''Convert binary back to string'''
        mapping = {
            32: 'DH',  # NEW
            16: 'E', 
            8: 'L', 
            4: 'D', 
            2: 'N', 
            1: '-'
        }
        return mapping.get(shift_int, '?')


class Nurse:
    def __init__(self, id, contract_id, skills, shift_off_requests, time_off_requests, weekend_composition_id):
        self.id = id
        self.contract_id = contract_id
        self.skills = skills
        self.shift_off_requests = shift_off_requests
        self.time_off_requests = time_off_requests
        self.weekend_composition_id = weekend_composition_id
    
    def __repr__(self):
        return f"Nurse(id={self.id}, contract={self.contract_id})"


class Contract:
    '''Represents a contract with constraints.'''
    
    def __init__(self, id, counterConstraints, seriesConstraints, 
                 patternConstraints=None, completeWeekends=None, identicalWeekends=None):
        self.id = id
        self.counterConstraints = counterConstraints
        self.seriesConstraints = seriesConstraints
        self.patternConstraints = patternConstraints if patternConstraints is not None else []
        self.completeWeekends = completeWeekends
        self.identicalWeekends = identicalWeekends
    
    @property
    def unwantedPatterns(self):
        '''Return pattern constraints (for compatibility with constraint checker).'''
        if not self.patternConstraints:
            return []
        # Handle both list and dict formats
        if isinstance(self.patternConstraints, list):
            return self.patternConstraints
        return []
    
    def __repr__(self):
        return f"Contract(id={self.id})"