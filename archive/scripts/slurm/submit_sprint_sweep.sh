#!/bin/bash --login
###
# Sprint Lc Sweep - Validation Run
# Confirms the project runs correctly on Falcon before committing to
# the full weekend sweep.
#
# BEFORE SUBMITTING: Replace scwXXXX with your actual SCW project code.
# Check available Python versions with: module avail python
###

#SBATCH --job-name=schc_sprint_sweep
#SBATCH --output=logs/sprint_sweep_%J.out
#SBATCH --error=logs/sprint_sweep_%J.err
#SBATCH --time=0-06:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --account=scwXXXX

# Print job info for debugging
echo "Job ID: $SLURM_JOB_ID"
echo "Running on node: $SLURMD_NODENAME"
echo "Start time: $(date)"
echo ""

# Load Python - check available versions first with: module avail python
# Update the version below to match what is available on Falcon
module purge
module load python/3.11.9

# Confirm Python version
python --version

# Move to project root (adjust this path to wherever you put the project on Falcon)
# This ensures relative paths like data/inrc1/... resolve correctly
cd $SLURM_SUBMIT_DIR

# Create logs directory if it does not exist
mkdir -p logs
mkdir -p outputs

echo "Working directory: $(pwd)"
echo "Starting sprint Lc sweep..."
echo ""

python test_sprint_lc_sweep.py

echo ""
echo "Sprint sweep complete at: $(date)"