from torch.utils.data import Dataset
from torchvision import transforms
import rasterio
import numpy as np


class DisasterDataset(Dataset):
    def __init__(self, chips_dir, masks_dir, transform=None):
        # Implement: load chip paths, load masks, etc.
        pass

    def __len__(self):
        # Return the number of chips
        pass

    def __getitem__(self, idx):
        # Return (chip, mask/label)
        pass


# Model: UNet, Mask R-CNN, etc.
# Training loop: Standard supervised segmentation/classification loop with chips and masks
# Inference: Predict on new chips → export GeoTIFF, visualize (steps below)
