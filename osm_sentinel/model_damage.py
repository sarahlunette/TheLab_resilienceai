# model_damage.py
from common_imports import *


class DoubleConv(nn.Module):
    """
    Bloc convolutionnel standard UNet : Conv -> BN -> ReLU -> Conv -> BN -> ReLU.
    """
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class UNet(nn.Module):
    """
    UNet encoder-decoder peu profond, adapté à des patches 256x256
    et à un petit nombre de classes (ex: 3).
    """
    def __init__(self, in_channels, n_classes):
        super().__init__()

        # Encoder
        self.down1 = DoubleConv(in_channels, 64)
        self.pool1 = nn.MaxPool2d(2)  # H/2, W/2
        self.down2 = DoubleConv(64, 128)
        self.pool2 = nn.MaxPool2d(2)  # H/4, W/4
        self.down3 = DoubleConv(128, 256)
        self.pool3 = nn.MaxPool2d(2)  # H/8, W/8

        # Bottleneck
        self.bottleneck = DoubleConv(256, 512)

        # Decoder
        self.up3 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec3 = DoubleConv(512, 256)   # concat(256,256)
        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec2 = DoubleConv(256, 128)
        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec1 = DoubleConv(128, 64)

        # Output head: logits par classe
        self.out_conv = nn.Conv2d(64, n_classes, 1)

    def forward(self, x):
        # Encoder
        c1 = self.down1(x)
        p1 = self.pool1(c1)
        c2 = self.down2(p1)
        p2 = self.pool2(c2)
        c3 = self.down3(p2)
        p3 = self.pool3(c3)

        # Bottleneck
        bn = self.bottleneck(p3)

        # Decoder
        u3 = self.up3(bn)
        # En cas de léger décalage spatial (padding), on pourrait cropper ici
        if u3.shape[-2:] != c3.shape[-2:]:
            # crop c3 vers la taille de u3
            c3 = c3[..., :u3.shape[-2], :u3.shape[-1]]
        m3 = torch.cat([u3, c3], dim=1)
        c3d = self.dec3(m3)

        u2 = self.up2(c3d)
        if u2.shape[-2:] != c2.shape[-2:]:
            c2 = c2[..., :u2.shape[-2], :u2.shape[-1]]
        m2 = torch.cat([u2, c2], dim=1)
        c2d = self.dec2(m2)

        u1 = self.up1(c2d)
        if u1.shape[-2:] != c1.shape[-2:]:
            c1 = c1[..., :u1.shape[-2], :u1.shape[-1]]
        m1 = torch.cat([u1, c1], dim=1)
        c1d = self.dec1(m1)

        # [B, n_classes, H, W] —> CrossEntropyLoss(y_long) OK
        return self.out_conv(c1d)
