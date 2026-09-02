"""Print the PyTorch/CUDA state used by Comfy Desktop."""

import torch


device = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"
print(f"PyTorch {torch.__version__}; CUDA={torch.cuda.is_available()}; device={device}")
