'''
Solution representation for Nurse Rostering Problem.
Uses 2D matrix with binary shift encoding.
'''

from models import ShiftType

class Solution:
    '''
    Represents a complete nurse roster.
    
    Schedule is a 2D matrix:
    - Rows: nurses (indexed by nurse ID)
    - Columns: days (0 to n_days-1)
    - Values: binary shift encoding (16, 8, 4, 2, 1)
    '''
    
    def __init__(self, n_nurses, n_days):
        # Initialize all to OFF (1)
        self.schedule = [[ShiftType.OFF] * n_days for _ in range(n_nurses)]
        self.n_nurses = n_nurses
        self.n_days = n_days
    
    def assign_shift(self, nurse_id, day, shift_type):
        '''Assign a shift (as binary int) to a nurse on a day'''
        self.schedule[nurse_id][day] = shift_type
    
    def get_assignment(self, nurse_id, day):
        '''Get what shift a nurse works on a day'''
        return self.schedule[nurse_id][day]
    
    def copy(self):
        '''Create a deep copy of this solution'''
        new_sol = Solution(self.n_nurses, self.n_days)
        new_sol.schedule = [row[:] for row in self.schedule]
        return new_sol
    
    def print_schedule(self):
        '''Pretty print the schedule (for debugging)'''
        for nurse_id, row in enumerate(self.schedule):
            shifts = [ShiftType.to_string(s) for s in row]
            print(f"Nurse {nurse_id}: {' '.join(shifts)}")