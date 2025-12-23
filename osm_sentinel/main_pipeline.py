# main_pipeline.py
from build_features import prepare_feature_stack
from train_damage import train_model
from infer_and_export import infer_full_scene

if __name__ == "__main__":
    prepare_feature_stack()   # Sentinel + OSM -> features.npy
    # create labels.npy aligned to AOI before training (from xBD/xView2 or your annotations)
    train_model()             # train UNet on your labeled patches
    infer_full_scene()        # produce full-scene damage_map.tif
