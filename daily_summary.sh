set -a
source "$(dirname "$0")/.env"
set +a

source ~/miniforge3/etc/profile.d/conda.sh
conda activate Arxiv-Summariser
cd /home/lewis/Desktop/Projects/arxiv_summariser/scripts
python daily_summary.py

