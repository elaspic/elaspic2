#!/bin/bash
#SBATCH --array=1-100
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --mem=120G
#SBATCH --account=rrg-pmkim
#SBATCH --job-name=run-notebook-cpu
#SBATCH --export=ALL
#SBATCH --mail-type=BEGIN
#SBATCH --mail-user=alexey.strokach@kimlab.org
#SBATCH --output=/lustre04/scratch/strokach/run-notebook-cpu-%N-%j.log

unset XDG_RUNTIME_DIR

mkdir ${SLURM_TMPDIR}/env
tar -xzf ~/datapkg-data-dir/conda-envs/default/default-v42.tar.gz -C ${SLURM_TMPDIR}/env

chmod ugo+rwX ${SLURM_TMPDIR}/env/bin/activate -R
# source ${SLURM_TMPDIR}/env/bin/activate
source ${SLURM_TMPDIR}/env/etc/profile.d/conda.sh
conda-unpack

sed -i "s|XXXX|${KEY_MODELLER}|" ${SLURM_TMPDIR}/env/lib/modeller-9.25/modlib/modeller/config.py

pip install ..

# jupyter lab --ip 0.0.0.0 --no-browser

NOTEBOOK_STEM=$(basename ${NOTEBOOK_PATH%%.ipynb})
NOTEBOOK_DIR=$(dirname ${NOTEBOOK_PATH})
OUTPUT_TAG="${SLURM_JOB_NODELIST}-${SLURM_JOB_ID}-${SLURM_ARRAY_JOB_ID}-${SLURM_ARRAY_TASK_ID}"

mkdir -p "${NOTEBOOK_DIR}/${NOTEBOOK_STEM}"
papermill --no-progress-bar --log-output --kernel python3 "${NOTEBOOK_PATH}" "${NOTEBOOK_DIR}/${NOTEBOOK_STEM}-${OUTPUT_TAG}.ipynb"
