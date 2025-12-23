# infer_and_export.py
from common_imports import *
from model_damage import UNet

def infer_full_scene():
    feat_path = os.path.join(OUT_DIR, "features.npy")
    C, H, W = np.load(feat_path).shape
    feat = np.load(feat_path)[np.newaxis, ...]  # [1,C,H,W]

    num_classes = 3
    model = UNet(in_channels=C, n_classes=num_classes)
    model.load_state_dict(torch.load(os.path.join(OUT_DIR, "damage_unet.pth"), map_location="cpu"))
    model.eval()

    with torch.no_grad():
        logits = model(torch.from_numpy(feat))
        pred = logits.argmax(dim=1).squeeze(0).numpy().astype(np.uint8)

    min_lon, min_lat, max_lon, max_lat = AOI_BBOX
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, W, H)
    out_tif = os.path.join(OUT_DIR, "damage_map.tif")
    with rasterio.open(
        out_tif, "w",
        driver="GTiff",
        height=H,
        width=W,
        count=1,
        dtype=pred.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(pred, 1)
    print("Saved damage map:", out_tif)
