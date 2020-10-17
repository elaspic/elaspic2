#!/bin/bash
#SBATCH --array=1-1
#SBATCH --time=72:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --mem=120G
#SBATCH --account=rrg-pmkim
#SBATCH --job-name=run-notebook-cpu
#SBATCH --export=ALL
#SBATCH --mail-type=BEGIN
#SBATCH --mail-user=alexey.strokach@kimlab.org
#SBATCH --output=logs/run-notebook-cpu-%N-%j.log

set -ev

unset XDG_RUNTIME_DIR

echo ${NOTEBOOK_PATH}

mkdir ${SLURM_TMPDIR}/env
tar -xzf ~/datapkg-data-dir/conda-envs/default/default-v43.tar.gz -C ${SLURM_TMPDIR}/env

source ${SLURM_TMPDIR}/env/etc/profile.d/conda.sh
source ${SLURM_TMPDIR}/env/bin/activate
chmod ugo+rwX ${SLURM_TMPDIR}/env/ -R
conda-unpack

sed -i "s|XXXX|${KEY_MODELLER}|" ${SLURM_TMPDIR}/env/lib/modeller-9.25/modlib/modeller/config.py

pip install --no-deps --no-use-pep517 -e ..

if [[ ${INTERACTIVE} = "true" ]] ; then
    jupyter lab --ip 0.0.0.0 --no-browser
    exit 0
fi

NOTEBOOK_STEM=$(basename ${NOTEBOOK_PATH%%.ipynb})
NOTEBOOK_DIR=$(dirname ${NOTEBOOK_PATH})
OUTPUT_TAG="${SLURM_ARRAY_JOB_ID}-${SLURM_ARRAY_TASK_ID}-${SLURM_JOB_NODELIST}-${SLURM_JOB_ID}"

mkdir -p "${NOTEBOOK_DIR}/${NOTEBOOK_STEM}"
papermill --no-progress-bar --log-output --kernel python3 "${NOTEBOOK_PATH}" "${NOTEBOOK_DIR}/${NOTEBOOK_STEM}-${OUTPUT_TAG}.ipynb"

