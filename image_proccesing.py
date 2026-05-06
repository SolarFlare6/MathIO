import numpy as np
import cv2 as cv
import pytesseract as pt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- helper: CONSTANT VARIABLES ----------
save_path: str = "Debug_Images"
def create_path(save__path, name_of_image):
    return str(Path(save_path, name_of_image))


# ---------- helper: order points ----------
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    return rect
# ---------- helper: DEBUG FUNC ----------
# Image Args should be ALWAYS DICTS with title,data KEYS.
def debug_plot(rows, cols, *images):
    fig, axes = plt.subplots(rows, cols, figsize=(16, 10), dpi=200)

    #FIX: normalize axes
    axes = np.array(axes)
    axes = axes.flatten()

    img_count = len(images)

    for i, ax in enumerate(axes):
        img = images[i % img_count]  # ✔ looping behavior

        ax.set_title(img["title"])
        ax.imshow(cv.cvtColor(img["data"], cv.COLOR_BGR2RGB))

    plt.tight_layout()
    plt.savefig(create_path(save_path, "debug_plot.jpg"))
    plt.close()

def process_image(selected_image_path, lang="eng", debug=False):

    # ---------- load image ----------
    img = cv.imread(selected_image_path)
    orig = img.copy()

    # ---------- preprocessing ----------
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY) # Transform Image into a GreyScale Image
    gray = cv.GaussianBlur(gray, (7, 7), 0)
    # cv.imwrite("./Debug_Images/gray.jpg", gray)

    # First threshold1 is used for small changed in between pixels to mark them, if point is next to another it will addit
    # Second threshold2 is used for big changes, if detected it adds the point, known as an anchor.
    edges = cv.Canny(gray, threshold1=75, threshold2=210) #OVDE SNAPSHOT
    if debug:
        image_pre_dilation = img.copy()
        contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        edges_image_pre_dilation = cv.drawContours(image_pre_dilation, contours , -1, (0, 255, 255), 5)

    # Kernel is used like a brush, if one pixel is white in dilate, takes that and expands the area
    # to fix broken points for better contours
    kernel = np.ones((5, 5), np.uint8)
    edges = cv.dilate(edges, kernel, iterations=2)
    edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel) #OVDE SNAPSHOT
    if debug:
        image_dilated = img.copy()
        contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        edges_image_dilated = cv.drawContours(image_dilated, contours , -1, (0, 0, 255), 5)

    # ---------- find contours ----------
    contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE) #If points touch one another, it is considered connected

    # Pick Largest contour of the given. Typically, we catch contour of  the A4 Paper but depends on the situation
    largest = max(contours, key=cv.contourArea)
    if debug:
        image_largest_contour = img.copy()
        largest_contour = cv.drawContours(image_largest_contour, [largest] , -1, (0, 255, 255), 5)
    # ---------- robust corner detection ----------

    # Takes the form of the contour and tries to create a convex Shape so that every point can each on another inside the area.
    hull = cv.convexHull(largest)
    # Gets Perimeter for the hull which will be used for creating an exact replica of our a4 paper shape.
    peri = cv.arcLength(hull, True)
    if debug:
        image_hull = img.copy()
        convex_hull = cv.drawContours(image_hull, [hull], -1, (0, 0, 255), 5)

    # Loop 10 times starting from 0.02 to 0.06 which each iteration will be equal distance from the
    # Previous i, this way we try to create the polygon with the simplest shape of the A4 Paper.
    approx = None
    for eps in np.linspace(0.02, 0.06, 10):
        candidate = cv.approxPolyDP(hull, eps * peri, True)
        if len(candidate) == 4:
            approx = candidate
            if debug:
                paper_image = img.copy()
                paper_display = cv.drawContours(paper_image, [approx], -1, (0, 255, 0), 10)
            break

    # If the paper is really complicated in terms of form, fallback to this variation.
    # Additional Explanation Tomorrow.
    if approx is None:
        rect = cv.minAreaRect(largest)
        box = cv.boxPoints(rect)
        if debug:
            paper_image = img.copy()
            paper_display = cv.drawContours(paper_image, [approx], -1, (0, 255, 0), 10)

        pts = np.array(box, dtype="float32")
    else:
        pts = approx.reshape(4, 2).astype("float32")
    # ---------- order points ----------
    pts = order_points(pts)
    if debug:
        points_paper = img.copy()
        for (x, y) in pts:
            cv.circle(points_paper, (int(x), int(y)), 30, (0, 0, 255), -1)
    # ---------- compute width & height ----------
    widthA = np.linalg.norm(pts[2] - pts[3])
    widthB = np.linalg.norm(pts[1] - pts[0])
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(pts[1] - pts[2])
    heightB = np.linalg.norm(pts[0] - pts[3])
    maxHeight = int(max(heightA, heightB))

    # ---------- destination points ----------
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    # ---------- perspective transform ----------
    M = cv.getPerspectiveTransform(pts, dst)
    warped = cv.warpPerspective(orig, M, (maxWidth, maxHeight))

    # ---------- show results ----------
    if debug:
        print("Will ADD TOMORROW WITH MATPLOT!!!")
        debug_plot(2,5, {"data": orig, "title": "Original Image"},
                   {"data": gray, "title": "Pre-processed Grayscale"},
                   {"data": edges_image_pre_dilation, "title": "Edges Pre-Dilation"},
                   {"data": edges_image_dilated, "title": "Pre-processed Edges Dilation"},
                   {"data": largest_contour, "title": "Largest Contour"},
                   {"data": convex_hull, "title": "Pre-processed Convex Hull"},
                   {"data": points_paper, "title": "Pre-processed Points Image"},
                   {"data": paper_display, "title": "Pre-processed A4 Paper Display"},
                   {"data": orig, "title": "Before: Original Image"},
                   {"data": warped, "title": "After:A4 Warped Perspective"},)
    return pt.image_to_string(warped, lang=lang) # Result send in string format
