import numpy as np
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


x1s = [852, 791, 420, 1337, 2077, 1252, 1759, 511, 416, 418, 856, 416, 396, 1506, 521, 425, 1743, 931, 524, 426, 1774, 437, 1778, 1082, 875, 449, 1665, 516, 444]
x2s = [2797, 2812, 1125, 1863, 2777, 1427, 1951, 2786, 2167, 2435, 2663, 2795, 2797, 2797, 2796, 2797, 2797, 2799, 2798, 2809, 2809, 2812, 2358, 2235, 2570, 2816, 2816, 2818, 2818]
yhs =[260, 77, 206, 125, 213, 35, 38, 131, 135, 71, 82, 548, 266, 46, 61, 84, 43, 57, 62, 437, 119, 263, 83, 52, 72, 93, 45, 55, 107]


def classify_paragraphs(x1s, x2s, yhs, minyh=100):
    x_coordinates = [(x, y, z) for x, y, z in zip(x1s, x2s, yhs)]
    print(x_coordinates)
    xw = (max(x2s)-min(x1s))/2
    x_coordinates = [(x, y) for x, y, z in x_coordinates if z>minyh and (y-x)>xw-100 and (y-x)<xw]

    # Extract x1 coordinates for normal paragraphs for clustering
    x1_coordinates = np.array([x[0] for x in x_coordinates]).reshape(-1, 1)

    # Apply K-means clustering to classify into left and right columns
    kmeans = KMeans(n_clusters=2, random_state=0).fit(x1_coordinates)
    labels = kmeans.labels_

    left_column = []
    right_column = []

    for coord, label in zip(x_coordinates, labels):
        if label == 0:
            left_column.append(coord)
        else:
            right_column.append(coord)

    print(left_column)
    print(right_column)

    # Calculate median x1 and x2 for left and right columns
    left_x1_median = np.median([x[0] for x in left_column])
    left_x2_median = np.median([x[1] for x in left_column])
    right_x1_median = np.median([x[0] for x in right_column])
    right_x2_median = np.median([x[1] for x in right_column])

    print({
        "left_column_median": (left_x1_median, left_x2_median),
        "right_column_median": (right_x1_median, right_x2_median),
    })


classify_paragraphs(x1s, x2s, yhs)
