#!/bin/bash --login
###
# Medium Instance Sweep - Slurm Job Array
# ========================================
# Submits 5 independent jobs, one per medium instance.
# Each job calls run_instance_sweep.py with its own index.
#
# Slurm assigns each job a unique $SLURM_ARRAY_TASK_ID (1 through 5),
# which maps directly to INRC1_medium01 through INRC1_medium05.
#
# Jobs run in parallel if compute nodes are available, which can
# reduce total wall time from sequential ~20h to ~4h per instance.
#
# Time limit per job: 8 hours.
# After the first instance completes, check its actual runtime and
# adjust --time for the long array if needed.
#
# BEFORE SUBMITTING:
#   1. Replace scwXXXX with your SCW project account code
#   2. Confirm Python module version with: module avail python
#   3. Update your email address
#
# SUBMIT WITH:
#   sbatch submit_medium_array.sh
#
# MONITOR WITH:
#   squeue -u $USER
#   tail -f logs/medium_01_<JOBID>.out    (or whichever index)
#
# CANCEL ALL WITH:
#   scancel -u $USER
###

#SBATCH --job-name=schc_medium
#SBATCH --output=logs/medium_%a_%A.out
#SBATCH --error=logs/medium_%a_%A.err
#SBATCH --array=1-5
#SBATCH --time=0-08:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --account=scwXXXX
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=YOUR_EMAIL@bangor.ac.uk

# %a is the array task index, %A is the parent job ID
# Each instance gets its own log file: medium_1_12345.out, medium_2_12345.out, etc.

echo "=============================================="
echo " SCHC Medium Instance Sweep"
echo "=============================================="
echo "Array task ID:  $SLURM_ARRAY_TASK_ID"
echo "Parent job ID:  $SLURM_ARRAY_JOB_ID"
echo "Node:           $SLURMD_NODENAME"
echo "Start:          $(date)"
echo "=============================================="
echo ""

module purge
module load python/3.11.9

echo "Python: $(python --version)"
echo ""

cd $SLURM_SUBMIT_DIR

mkdir -p logs
mkdir -p outputs

# Confirm the instance file exists before starting
INSTANCE_FILE="data/inrc1/INRC1_medium$(printf '%02d' $SLURM_ARRAY_TASK_ID).json"
if [ ! -f "$INSTANCE_FILE" ]; then
    echo "ERROR: Instance file not found: $INSTANCE_FILE"
    echo "Check your data/inrc1/ directory structure."
    exit 1
fi

echo "Instance file confirmed: $INSTANCE_FILE"
echo ""

python run_instance_sweep.py medium $SLURM_ARRAY_TASK_ID

EXIT_CODE=$?

echo ""
echo "=============================================="
echo " Medium instance $SLURM_ARRAY_TASK_ID finished"
echo " Exit code: $EXIT_CODE"
echo " End time:  $(date)"
echo "=============================================="

exit $EXIT_CODE