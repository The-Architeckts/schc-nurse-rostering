'''
Data models for Nurse Rostering Problem.
Represents nurses, contracts, shift types, etc.
'''

class ShiftType:
    '''Binary encoding for shifts'''
    E = 16     # 0b10000 - Early
    L = 8      # 0b01000 - Late
    D = 4      # 0b00100 - Day
    N = 2      # 0b00010 - Night
    OFF = 1    # 0b00001 - Day off
    
    @staticmethod
    def from_string(shift_str):
        '''Convert 'E', 'L', 'D', 'N' to binary'''
        mapping = {'E': ShiftType.E, 'L': ShiftType.L, 
                   'D': ShiftType.D, 'N': ShiftType.N}
        return mapping.get(shift_str, ShiftType.OFF)
    
    @staticmethod
    def to_string(shift_int):
        '''Convert binary back to 'E', 'L', 'D', 'N', '-' '''
        mapping = {16: 'E', 8: 'L', 4: 'D', 2: 'N', 1: '-'}
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
    def __init__(self, id, counterConstraints, seriesConstraints, patternConstraints, 
                 completeWeekends, identicalWeekends):
        self.id = id
        self.counterConstraints = counterConstraints
        self.seriesConstraints = seriesConstraints
        self.patternConstraints = patternConstraints
        self.completeWeekends = completeWeekends
        self.identicalWeekends = identicalWeekends
    
    def __repr__(self):
        return f"Contract(id={self.id})"