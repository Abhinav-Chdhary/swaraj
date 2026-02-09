#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="swaraj"

echo "=== Swaraj Backend Setup ==="

# 1. Create conda environment
if conda info --envs | grep -q "^${ENV_NAME} "; then
    echo "Conda env '${ENV_NAME}' already exists, skipping creation."
else
    echo "Creating conda env '${ENV_NAME}' with python=3.10..."
    conda create -y -n "${ENV_NAME}" python=3.10
fi

# Activate env for the rest of the script
eval "$(conda shell.bash hook)"
conda activate "${ENV_NAME}"

# 2. Install PyTorch
echo "Installing PyTorch..."
pip install torch torchvision torchaudio

# 3. Install supporting packages
echo "Installing packaging and huggingface_hub..."
pip install packaging huggingface_hub==0.23.2

# 4. Install FastAPI stack
echo "Installing FastAPI, uvicorn, python-multipart..."
pip install fastapi "uvicorn[standard]" python-multipart

# 5. Clone and install AI4Bharat NeMo fork
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEMO_DIR="${SCRIPT_DIR}/NeMo"

if [ -d "${NEMO_DIR}" ]; then
    echo "NeMo directory already exists, skipping clone."
else
    echo "Cloning AI4Bharat/NeMo (nemo-v2 branch)..."
    git clone -b nemo-v2 https://github.com/AI4Bharat/NeMo.git "${NEMO_DIR}"
fi

echo "Installing NeMo..."
cd "${NEMO_DIR}"
bash reinstall.sh
cd "${SCRIPT_DIR}"

# 6. Download the Hindi IndicConformer model checkpoint
echo "Downloading IndicConformer Hindi model from HuggingFace..."
python -c "
import nemo.collections.asr as nemo_asr
model = nemo_asr.models.ASRModel.from_pretrained(
    'ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large'
)
print('Model downloaded successfully.')
"

echo ""
echo "=== Setup complete! ==="
echo "Run the server with:"
echo "  conda activate ${ENV_NAME}"
echo "  cd ${SCRIPT_DIR}"
echo "  uvicorn main:app --port 8000"
