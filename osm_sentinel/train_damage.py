# train_damage.py
from common_imports import *
from model_damage import UNet

class DamageDataset(Dataset):
    def __init__(self, feat_path, label_path, patch_size=256):
        self.feat = np.load(feat_path)  # [C,H,W]
        self.lab = np.load(label_path)  # [H,W] int classes 0..K-1
        self.C, self.H, self.W = self.feat.shape
        self.ps = patch_size

    def __len__(self):
        return 64  # random patches for simplicity

    def __getitem__(self, idx):
        i = np.random.randint(0, self.H - self.ps)
        j = np.random.randint(0, self.W - self.ps)
        x = self.feat[:, i:i+self.ps, j:j+self.ps]
        y = self.lab[i:i+self.ps, j:j+self.ps]
        return torch.from_numpy(x), torch.from_numpy(y).long()

def train_model():
    feat_path = os.path.join(OUT_DIR, "features.npy")
    # You must create label raster aligned with AOI (e.g., from xBD/xView2, or manual labels)
    label_path = os.path.join(OUT_DIR, "labels.npy")

    ds = DamageDataset(feat_path, label_path)
    dl = DataLoader(ds, batch_size=4, shuffle=True)

    C, _, _ = np.load(feat_path).shape
    num_classes = 3  # 0=background,1=intact,2=damaged (or any mapping)
    model = UNet(in_channels=C, n_classes=num_classes)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(10):
        model.train()
        total_loss = 0.0
        for x, y in dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            opt.step()
            total_loss += loss.item()
        print(f"Epoch {epoch}: loss={total_loss/len(dl):.4f}")

    torch.save(model.state_dict(), os.path.join(OUT_DIR, "damage_unet.pth"))
