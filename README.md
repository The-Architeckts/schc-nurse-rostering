Applying SCHC to Nurse Rostering ProblemUndergraduate dissertation project investigating the application of Step Counting Hill Climbing algorithm to the Nurse Rostering Problem using INRC-I benchmark datasets.## AuthorArthur - [Your University]## Project OverviewThis project explores a novel application of the Step Counting Hill Climbing (SCHC) algorithm to the Nurse Rostering Problem (NRP). No prior work has applied SCHC to NRP, representing a research gap in the optimization literature.

Project Structure

Code/
├── data/inrc1/ # INRC-I benchmark instances
├── src/
│ ├── models.py # Data structures (Nurse, Contract, ShiftType)
│ ├── data_loader.py # JSON parsing
│ ├── solution.py # 2D matrix representation
│ ├── constraints.py # Penalty calculation
│ ├── constructors.py # Greedy baseline generator
│ └── data_analyser.py # Testing/validation
└── docs/ # Documentation (future)

Current Status
- ✅ Data loading from INRC-I JSON format
- ✅ Solution representation (2D matrix with binary encoding)
- ✅ Greedy baseline constructor (penalty: 32)- ✅ Counter constraint evaluation
- ⏳ Hill Climbing implementation (next)- ⏳ SCHC implementation## Setup & RunningNo external dependencies required (pure Python stdlib).
bash# Navigate to project directorycd Code/# Run the baseline constructor testpython src/data_analyser.py

Results So Far

Baseline Solution (Greedy Round-Robin Constructor):
- Instance: INRC-I sprint01
- Nurses: 10
- Days: 28
- Penalty: 32 (soft constraint violations only)
- All hard constraints satisfied (feasible solution)

Next Steps
2. Implement Hill Climbing (Lc=0)
4. Implement SCHC-all (Lc>0)
6. Compare performance on sprint/medium/long instances
8. Analyze scalability and convergence behavior

References
- Burke, E. K., & Bykov, Y. (2016). A Step Counting Hill Climbing Algorithm applied to University Examination Timetabling. *Journal of Scheduling*.
- Haspeslagh, S., et al. (2014). The first international nurse rostering competition 2010. *Annals of Operations Research*.