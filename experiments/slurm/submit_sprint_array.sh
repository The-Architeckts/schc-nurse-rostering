#!/bin/bash --login
# Slurm job array: one task per INRC-I sprint instance (1-10).
# Each task runs HC plus all three SCHC variants across the full Lc sweep.
#
# Submit from the repository root:
#     sbatch experiments/slurm/submit_sprint_array.sh
#
# Set --account to your own project code before submitting. Module names
# are those used on the Supercomputing Wales Falcon cluster.
#SBATCH --job-name=schc_sprint
#SBATCH --output=logs/sprint_%a_%A.out
#SBATCH --error=logs/sprint_%a_%A.err
#SBATCH --array=1-10
#SBATCH --time=0-06:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --account=YOUR_PROJECT_ACCOUNT
#SBATCH --partition=htc_genoa

echo "Sprint | Instance: $SLURM_ARRAY_TASK_ID | Node: $SLURMD_NODENAME | Start: $(date)"

module purge
module load Python/3.12.3-GCCcore-13.3.0
module load Python-bundle-PyPI/2024.06-GCCcore-13.3.0

cd $SLURM_SUBMIT_DIR
mkdir -p logs outputs

INSTANCE_FILE="data/inrc1/INRC1_sprint$(printf '%02d' $SLURM_ARRAY_TASK_ID).json"
if [ ! -f "$INSTANCE_FILE" ]; then
    echo "ERROR: $INSTANCE_FILE not found"; exit 1
fi

python experiments/run_instance_sweep.py sprint $SLURM_ARRAY_TASK_ID

EXIT_CODE=$?
echo "Sprint instance $SLURM_ARRAY_TASK_ID done | Exit: $EXIT_CODE | End: $(date)"
exit $EXIT_CODE
