import csv
import os
import sys
from PIL import Image
import numpy as np


def analyze_luminosity(image_path):
    # Open and convert image to grayscale
    img = Image.open(image_path).convert('L')
    arr = np.array(img)
    # Average luminosity for each column
    luminosity = arr.mean(axis=0)

    mid = len(luminosity) // 2
    left = luminosity[:mid]
    right = luminosity[-mid:][::-1]  # Reverse the right half
    luminosity = (left + right) / 2

    binned = np.array_split(luminosity, 21)
    luminosity = np.array([slot.mean() for slot in binned])

    luminosity = luminosity / 100

    return luminosity


def main():
    # image_path = "F:\\Projects\\MEPIS\\LGP\\dist-0.8-0.005-size-0.5-0.0-2_sides\\test-2025-06-17-mirror-crop.jpg"
    image_path = "F:\\Projects\\MEPIS\\LGP\\dist-0.8-0.005-size-0.5-0.0-2_sides\\test-2025-06-17-white-crop.jpg"
    luminosity = analyze_luminosity(image_path)

    image_path_wout_ext = os.path.splitext(image_path)[0]

    with open(f"{image_path_wout_ext}.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['index', 'luminosity'])
        for idx, value in enumerate(luminosity):
            row_idx = idx/(len(luminosity) - 1) * 100
            writer.writerow([row_idx, value])


if __name__ == '__main__':
    main()
