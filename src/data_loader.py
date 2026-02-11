'''
Load INRC-I JSON instances into Python objects.
'''

import json
from models import Nurse, Contract

def load_instance(filepath):
    '''
    Load INRC-I instance from JSON file.
    Returns: dict with 'nurses', 'contracts', 'coverage', etc.
    '''
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Parse contracts
    contracts = {}
    for contract_data in data['instanceDefinitions']['constraintSets']:
        contract = Contract(
            id=contract_data['id'],
            counterConstraints=contract_data['counterConstraints'],
            seriesConstraints=contract_data['seriesConstraints'],
            patternConstraints=contract_data['patternConstraints'],
            completeWeekends=contract_data.get('completeWeekends'),
            identicalWeekends=contract_data.get('identicalWeekends')
        )
        contracts[contract.id] = contract
    
    # Parse nurses
    nurses = []
    for employee_data in data['employees']:
        nurse = create_nurse_from_json(employee_data)
        nurses.append(nurse)
    
    # Parse weekend compositions
    weekend_compositions = {}
    for weekend_data in data['instanceDefinitions']['weekendCompositions']:
        weekend_compositions[weekend_data['id']] = weekend_data
    
    return {
        'name': data['name'],
        'period': data['period']['horizon'],
        'start_day': data['period']['startDay'],
        'nurses': nurses,
        'contracts': contracts,
        'coverage': data['coverageRequirements'],
        'shift_types': data['instanceDefinitions']['shiftTypes'],
        'weekend_compositions': weekend_compositions
    }


def create_nurse_from_json(employee_data):
    '''Helper: Create Nurse object from JSON employee data'''
    return Nurse(
        id=employee_data['id'],
        contract_id=employee_data['constraintSetId'],
        skills=[skill['skillTypeId'] for skill in employee_data['skillTypes']],
        shift_off_requests=employee_data['requests']['shiftOffRequests'],
        time_off_requests=employee_data['requests']['timeOffRequests'],
        weekend_composition_id=employee_data['weekendCompositionId']
    )