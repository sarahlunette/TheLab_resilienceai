import rasterio
import matplotlib.pyplot as plt


def plot_tiff(filename):
    with rasterio.open(filename) as src:
        image = src.read()
        plt.imshow(np.moveaxis(image[:3], 0, -1))
        plt.show()
