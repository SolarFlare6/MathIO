import numpy as np
import cv2 as cv
import pytesseract as pt


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


def process_image(selected_image_path, lang="eng", debug=False):

    # ---------- load image ----------
    img = cv.imread(selected_image_path)
    orig = img.copy()

    # ---------- preprocessing ----------
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY) # Transform Image into a GreyScale Image
    gray = cv.GaussianBlur(gray, (7, 7), 0)
    cv.imwrite("./Debug_Images/gray.jpg", gray)

    # First threshold1 is used for small changed in between pixels to mark them, if point is next to another it will addit
    # Second threshold2 is used for big changes, if detected it adds the point, known as an anchor.
    edges = cv.Canny(gray, threshold1=75, threshold2=210) #OVDE SNAPSHOT

    # Kernel is used like a brush, if one pixel is white in dilate, takes that and expands the area
    # to fix broken points for better contours
    kernel = np.ones((5, 5), np.uint8)
    edges = cv.dilate(edges, kernel, iterations=2)
    edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel)

    # ---------- find contours ----------
    contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE) #If points touch one another, it is considered connected

    # Pick Largest contour of the given. Typically, we catch contour of  the A4 Paper but depends on the situation
    largest = max(contours, key=cv.contourArea)

    # ---------- robust corner detection ----------

    # Takes the form of the contour and tries to create a convex Shape so that every point can each on another inside the area.
    hull = cv.convexHull(largest)
    # Gets Perimeter for the hull which will be used for creating an exact replica of our a4 paper shape.
    peri = cv.arcLength(hull, True)

    # Loop 10 times starting from 0.02 to 0.06 which each iteration will be equal distance from the
    # Previous i, this way we try to create the polygon with the simplest shape of the A4 Paper.
    approx = None
    for eps in np.linspace(0.02, 0.06, 10):
        candidate = cv.approxPolyDP(hull, eps * peri, True)
        if len(candidate) == 4:
            approx = candidate
            break

    # If the paper is really complicated in terms of form, fallback to this variation.
    # Additional Explanation Tomorrow.
    if approx is None:
        rect = cv.minAreaRect(largest)
        box = cv.boxPoints(rect)
        pts = np.array(box, dtype="float32")
    else:
        pts = approx.reshape(4, 2).astype("float32")
    # ---------- order points ----------
    pts = order_points(pts)

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
        cv.imwrite("./Debug_Images/warped.jpg", warped)


    return pt.image_to_string(warped, lang=lang) # Result send in string format
