
# Applying Step Counting Hill Climbing to Nurse Rostering Problem
**Undergraduate Dissertation Project**
**Author:** Arthur Armstrong
**Institution:** Bangor University
**Academic Year:** 2025/2026
---
## Project Overview
This dissertation explores the novel application of the **Step Counting Hill Climbing (SCHC)** algorithm to the **Nurse Rostering Problem (NRP)**. No prior published work has applied SCHC to NRP, representing a clear research gap in optimisation literature.
The project uses the **INRC-I (First International Nurse Rostering Competition)** benchmark instances as the testing framework.
### Research Questions
1. **Can SCHC effectively optimise nurse rostering schedules?**
2. **How does SCHC compare to standard Hill Climbing (HC)?**
3. **Which neighbourhood operators are most effective for NRP?**
4. **Does the step counting mechanism (Lc) improve solution quality over greedy HC?**
---
## Current Status
✅ **Completed:**
- Data loading and parsing (INRC-I JSON format)
- Solution representation (2D matrix, binary shift encoding)
- Greedy baseline constructor
- Complete constraint evaluation (7 soft + 2 hard constraints)
- Neighbourhood operators (6 high-performing operators)
- Hill Climbing implementation (baseline for SCHC comparison)
- Comprehensive testing framework

⏳ **In Progress:**
- SCHC implementation (Lc > 0)

❌ **Planned:**
- HC vs SCHC comparison
- Scaling to medium/long instances
- Statistical analysis
- Final dissertation write-up
---
## Key Results (Preliminary - Sprint01 Instance)

**Baseline Solution:**
- Penalty: 254 (feasible)
- Generated using greedy round-robin constructor

**Hill Climbing Optimisation:**
- Final penalty: 63-68 (best: 63)
- Improvement: 73-75% (186-191 penalty reduction)
- Convergence: ~4,200 iterations, ~2.5 seconds
- Very consistent: StdDev = 2.7 across 10 runs

**Constraint-Level Improvements:**
- Series constraints: 102 → 2 (98% reduction) ⭐
- Pattern constraints: 19 → 0 (100% elimination) ⭐
- Complete weekends: 32 → 6 (81% reduction)
- Time-off requests: 63 → 29 (54% reduction)
- Counter constraints: 32 → 30 (6% reduction)

**Most Effective Operators:**
1. Swap Pattern (4.4% acceptance rate)
2. Three-Nurse Rotation (4.2% acceptance rate)
3. Cyclic Swap (3.2% acceptance rate)
---
## Project Structure
Code/

├── data/

│ └── inrc1/

│ ├── INRC1_sprint01.json # Test instance (10 nurses, 28 days)

│ └── [other instances...]

│

├── src/

│ ├── algorithms/

│ │ ├── **init**.py

│ │ └── hill_climbing.py # HC and Steepest Descent HC

│ │

│ ├── tests/

│ │ ├── **init**.py

│ │ ├── test_hc.py # HC comprehensive testing

│ │ ├── test_operators.py # Operator validation

│ │ ├── test_hard_constraints.py # Hard constraint testing

│ │ └── data_analyser.py # Baseline analysis

│ │

│ ├── models.py # Data structures (Nurse, Contract, ShiftType)

│ ├── data_loader.py # INRC-I JSON parsing

│ ├── solution.py # 2D matrix solution representation

│ ├── constraints.py # Constraint evaluation (all 7+2 types)

│ ├── constructors.py # Greedy baseline constructor

│ └── operators.py # 6 neighbourhood operators

│

├── docs/ # Documentation and reports

├── README.md # This file

└── .gitignore

## Implementation Details
### Constraint Evaluation
**Hard Constraints (Must be satisfied):**
- ✅ Coverage requirements: All shifts adequately staffed
- ✅ Single assignment: Max one shift per nurse per day
- **Penalty:** 10⁶ per violation (ensures feasibility maintained)

**Soft Constraints (Minimise violations):**
- ✅ Counter constraints: Min/max days worked per contract
- ✅ Series constraints: Min/max consecutive working/idle days
- ✅ Pattern constraints: Forbidden shift sequences (e.g., Late→Day)
- ✅ Complete weekends: Work all or no days of weekend
- ✅ Identical weekends: Same shift type on all weekend days
- ✅ Shift-off requests: Nurse prefers not to work specific shift
- ✅ Time-off requests: Nurse requests complete day off
- **Penalty:** +1 per violation

**Total Penalty Formula:**
```
penalty = (hard_violations × 10⁶) + soft_violations
```
### Neighbourhood Operators
6 operators retained after testing:
1. **Swap Shifts (Same Day)** - Exchange two nurses' shifts on one day
2. **Swap All Shifts (Two Days)** - 2×2 swap pattern between nurses
3.  **Cyclic Swap** - 4-way rotation between 2 nurses, 2 days
4.  **Move Pattern** - Move 2-3 consecutive shifts between nurses
5.  **Swap Pattern** - Exchange 2-3 consecutive shifts between nurses
6.  **Three-Nurse Rotation** - Rotate shifts among 3 nurses on one day
	
  **Design principles:**
	- All swap-based (maintain coverage)
	- All feasibility-preserving (no hard constraint violations)
	- Pattern-based operators most effective (target series constraints)
	
  **Removed operators:**
	- ❌ Single Shift Change (0% feasibility - breaks coverage)
	- ❌ Change Shift Type (0% feasibility - breaks coverage)
	- ❌ Swap Shifts (Same Nurse) (0% acceptance - ineffective)

  ### Hill Climbing Algorithm

  **Standard HC (Random Operator Selection):**
	
  ```python
	while idle_iterations < max_idle:
	    neighbor = random_operator(current_solution)
	    if penalty(neighbor) < penalty(current):
	        current = neighbor  # Accept (greedy)
	        idle_iterations = 0
	    else:        
	idle_iterations += 1
```

**Steepest Descent HC (Best Operator Selection):**

```python
while idle_iterations < max_idle:    
    best_neighbor = None    
    for operator in all_operators:        
        neighbor = operator(current_solution)        
    if penalty(neighbor) < penalty(best_neighbor):
            best_neighbor = neighbor        
    if penalty(best_neighbor) < penalty(current):
        current = best_neighbor  # Accept best        
    idle_iterations = 0    
else:        
    idle_iterations += 1
```

**Convergence:** Stops after 1,000 consecutive non-improving iterations
---

## How to Run
### Prerequisites
- Python 3.12+ (no external dependencies for core functionality)- Optional: `matplotlib` for convergence plots
### Running the Tests
```bash
# Navigate to project root
cd Code/
# Run baseline analysis
python src/tests/data_analyser.py
# Test neighbourhood operators
python src/tests/test_operators.py
# Test hard constraints
python src/tests/test_hard_constraints.py
# Run Hill Climbing optimisation
python src/tests/test_hc.py
```
### Expected Output
**HC Test Output:**
- Original baseline schedule visualisation
- Optimisation progress (penalty reduction over time)
- Operator usage statistics
- Final optimised schedule
- Constraint breakdown comparison
- Convergence plot (saved as `hc_convergence.png`)
---
## Key Findings
### 1. Operator Design Matters
**Successful patterns:**
- ✅ Pattern-based (2-3 consecutive shifts)
- ✅ Multi-nurse (2-3 nurses involved)
- ✅ Swap-based (exchange, not add/remove)
**Unsuccessful patterns:**
- ❌ Single-shift changes (break coverage)
- ❌ Single-nurse focus (can't solve inter-nurse problems)
### 2. Series Constraints Dominate
- **40%** of baseline penalty from series violations
- **98%** reduction achieved by HC
- Pattern-based operators specifically target this
### 3. Counter Constraints Are Stubborn
- Only **6%** reduction possible
- Fundamental structural constraint
- Trade-off with coverage requirements
- Expected behaviour (literature confirms)
### 4. High Consistency Achieved
- Standard deviation: 2.7 (only 4% variance)
- All 10 runs achieved >70% improvement
- Algorithm is reliable and repeatable
---
## Technical Decisions & Rationale
### Why 2D Matrix Representation?
- **O(1)** access to any nurse's assignment
- Easy constraint checking (consecutive patterns, weekends)
- Standard in NRP literature
- Memory efficient for instances up to ~100 nurses
### Why Binary Shift Encoding?
```python
OFF = 1 # 0b00001
Night = 2 # 0b00010
Day = 4 # 0b00100
Late = 8 # 0b01000
Early = 16 # 0b10000
```
- Fast bitwise operations
- Easy validation (only one bit set = valid shift)
- Extensible to more shift types
### Why Greedy Baseline Constructor?
- **Fast:** Generates solution in <0.1 seconds
- **Feasible:** Guarantees hard constraints satisfied
- **Realistic:** Mimics manual scheduling approach
- **Improvable:** Intentionally leaves optimisation opportunities
### Why Remove "Swap Shifts (Same Nurse)"?
- **0% acceptance rate** across 640 attempts
- Wastes computation (15% of operator attempts)
- NRP is inter-nurse problem, not intra-nurse
- Removal improved efficiency with no quality loss
---
## Literature Foundation
**Primary References:**

1. **Burke, E. K., & Bykov, Y. (2016).** "A Step Counting Hill Climbing Algorithm applied to University Examination Timetabling." *Journal of Scheduling, 19*(4), 479-492.
    - Source of SCHC algorithm
    - Counter mechanism and acceptance bounds

2. **Haspeslagh, S., et al. (2014).** "The first international nurse rostering competition 2010." *Annals of Operations Research, 218*(1), 221-236.
    - INRC-I competition description
    - Benchmark instance definitions

3. **Hybridisation papers** (Harmony Search, Genetic Algorithms, etc.)
    - Source of neighbourhood operator designs
    - NRP-specific heuristics
---
## Limitations & Future Work
### Current Limitations
2. **Testing scope:** Only sprint01 instance tested thoroughly
4. **Training data:** No test set validation yet
6. **Scalability:** Not yet tested on medium/long instances (30-50 nurses)
8. **Baseline only:** HC implemented as comparison baseline for SCHC
### Planned Extensions
**Immediate:**
- Implement SCHC with counter mechanism (Lc > 0)
- Test SCHC-all, SCHC-acp, SCHC-imp variants
- Compare HC vs SCHC on sprint01
- Analyse impact of Lc parameter
**Short-term:**
- Scale to medium instances (~30 nurses)
- Scale to long instances (~50 nurses, 56 days)
- Test on multiple data instances for robustness
- Statistical significance testing
**Potential (If time permits):**
- Hybrid approaches (SCHC + Simulated Annealing)
- Adaptive operator selection
- Incremental constraint evaluation
---
## Dependencies
**Core (Required):**
- Python 3.12+
- Standard library only (json, random, time, pathlib)
**Optional:**
- `matplotlib>=3.7.0` - Convergence plot visualisation
**Install optional dependencies:**
```bash
pip install matplotlib
```
---
## Repository Statistics
**Code Metrics:**
- Total lines: ~1,100
- Python files: 12
- Test coverage: Comprehensive (all constraints, all operators)
- Documentation: Inline comments + this README
**Git Activity:**
- Commits: 9
- Branches: main
- Last updated: 11/03/2026
---
## Contact & Supervision
**Student:** Arthur Armstrong

**Supervisor:** Mosab Bazargani

**Institution:** Bangor University School of Computer Science

**Project Duration:** October 2025 - May 2026

---
## License
This is academic coursework. Code may not be reused without permission from the author and institution.
---
## Acknowledgments
- INRC-I competition organisers for benchmark instances
- Burke & Bykov for SCHC algorithm foundation
- Mosab Bazargani for guidance and feedback
- NRP research community for operator design inspiration
---
**Last Updated:** 11/03/2026

**Project Status:** Active Development
---
## Quick Start Guide

**For someone new to the project:**

1. **Clone and explore:**
```bash
git clone [your-repo-url]
cd Codels src/ # See project structure
```
2. **Understand the baseline:**
```bash
python src/tests/data_analyser.py
```
Outputs: Baseline schedule and constraint breakdown
3. **Test operators:**
```bash
python src/tests/test_operators.py
```
Outputs: Which operators work and why
4. **Run optimisation:**
```bash
python src/tests/test_hc.py
```
Outputs: Full HC optimisation with before/after comparison
5. **Review results:**
- Check terminal output for penalty improvements
- View `hc_convergence.png` for convergence visualisation
- Compare baseline vs optimised schedules
---
**Questions? Issues? Suggestions?**
Contact: rtr22yht@bangor.ac.uk