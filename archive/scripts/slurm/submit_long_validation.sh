#!/bin/bash --login
###
# Long Instance Validation Test
# A short sanity check confirming long instances run correctly before
# committing to the full weekend sweep.
# Expected runtime: 30-90 minutes. Requesting 4 hours as buffer.
#
# BEFORE SUBMITTING: Replace scwXXXX with your actual SCW project code.
###

#SBATCH --job-name=schc_long_validation
#SBATCH --output=logs/long_validation_%J.out
#SBATCH --error=logs/long_validation_%J.err
#SBATCH --time=0-04:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --account=scwXXXX

echo "Job ID: $SLURM_JOB_ID"
echo "Running on node: $SLURMD_NODENAME"
echo "Start time: $(date)"
echo ""

module purge
module load python/3.11.9

python --version

cd $SLURM_SUBMIT_DIR

mkdir -p logs
mkdir -p outputs

echo "Working directory: $(pwd)"
echo "Starting long instance validation..."
echo ""

python test_long_validation.py

echo ""
echo "Long validation complete at: $(date)"