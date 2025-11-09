import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO

def quantize_spotify_image(n_colors=5):
    # Download and prepare the image
    url = "https://i.scdn.co/image/ab67616d0000b273e5e0ed0b19a6c10a3c075087"
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    img = img.resize((200, 200))
    pixels = np.array(img).reshape((-1, 3)).astype(np.float32)

    # Apply KMeans clustering
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, n_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    # Reconstruct quantized image
    centers = np.uint8(centers)
    quantized = centers[labels.flatten()]
    quantized_image = quantized.reshape((200, 200, 3))

    # Find dominant color
    label_counts = np.bincount(labels.flatten())
    dominant_index = np.argmax(label_counts)
    dominant_color = centers[dominant_index]
    r, g, b = map(int, dominant_color)
    print(f"Most used color (RGB): ({r}, {g}, {b})")

    # Display image
    cv2.imshow("Quantized Spotify Image", cv2.cvtColor(quantized_image, cv2.COLOR_RGB2BGR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    quantize_spotify_image()
