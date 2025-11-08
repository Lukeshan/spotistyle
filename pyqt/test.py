import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Step 1: Select image via OS popup
def select_image():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select an image", filetypes=[("Image files", "*.jpg *.png *.jpeg")])
    return file_path

# Step 2: Load and resize image
def load_pixels(image_path, size=(100, 100)):
    img = Image.open(image_path).convert("RGB")
    img = img.resize(size)
    pixels = np.array(img).reshape(-1, 3)
    return pixels

# Step 3: Plot pixels in RGB space
def plot_rgb_pixels(pixels):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
    ax.scatter(r, g, b, c=pixels / 255.0, marker='o', alpha=0.6)

    # RGB triangle corners
    corners = np.array([
        [255, 0, 0],   # Red
        [0, 255, 0],   # Green
        [0, 0, 255]    # Blue
    ])
    ax.plot_trisurf(corners[:, 0], corners[:, 1], corners[:, 2], color='gray', alpha=0.2)

    ax.set_xlabel("Red")
    ax.set_ylabel("Green")
    ax.set_zlabel("Blue")
    ax.set_title("RGB Pixel Distribution")
    plt.show()

# Run the script
if __name__ == "__main__":
    image_path = select_image()
    if image_path:
        pixels = load_pixels(image_path)
        plot_rgb_pixels(pixels)
    else:
        print("No image selected.")
