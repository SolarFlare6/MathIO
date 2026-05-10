import numpy as np
import cv2 as cv
import pytesseract as pt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
# from sympy.parsing.latex import parse_latex
# from sympy import solve

# ---------- helper: CONSTANT VARIABLES ----------
save_path: str = "Debug_Images"
verify_path: str = "Verify_Images"
def create_path(save__path, name_of_image):
    return str(Path(save__path, name_of_image))


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

def process_image(selected_image_path, lang="eng", debug=False, verify=False):

    # ---------- load image ----------
    img = cv.imread(selected_image_path)
    if img is None:
        raise Exception("Image could not be loaded")

    orig = img.copy()

    # ---------- INIT VARIABLES FOR DEBUG ----------
    edges_image_pre_dilation = orig.copy()
    edges_image_dilated = orig.copy()
    largest_contour = orig.copy()
    convex_hull = orig.copy()
    points_paper = orig.copy()
    paper_display = orig.copy()

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
    # ---------- Kernel Adjustments ----------
    # Kernel is used like a brush, if one pixel is white in dilate, takes that and expands the area
    # to fix broken points for better contours

    kernels = [
        np.ones((5, 5), np.uint8),
        np.ones((3, 3), np.uint8),
        np.ones((7, 7), np.uint8)
    ]

    contours = None
    largest = None
    used_edges = None
    pts = None

    for kernel in kernels:

        # apply dilation (expands white regions to connect broken edges)
        temp_edges = cv.dilate(edges, kernel, iterations=2)

        # MORPH_CLOSE fills small gaps between edges to form closed shapes
        temp_edges = cv.morphologyEx(temp_edges, cv.MORPH_CLOSE, kernel)  # OVDE SNAPSHOT

        if debug:
            image_dilated = img.copy()

            # we visualize what contours we get after this kernel version
            contours_debug, _ = cv.findContours(
                temp_edges,
                cv.RETR_EXTERNAL,
                cv.CHAIN_APPROX_SIMPLE
            )

            edges_image_dilated = cv.drawContours(
                image_dilated,
                contours_debug,
                -1,
                (0, 0, 255),
                5
            )

        # ---------- find contours ----------
        # If points touch one another, it is considered connected
        contours_try, _ = cv.findContours(
            temp_edges,
            cv.RETR_EXTERNAL,
            cv.CHAIN_APPROX_SIMPLE
        )

        if not contours_try:
            print("we continue")
            continue

        # Pick Largest contour of the given.
        largest_try = max(contours_try, key=cv.contourArea)

        # safety check: ignore tiny/noisy contours
        if cv.contourArea(largest_try) < 1000:
            continue

        # ---------- robust corner detection ----------
        hull = cv.convexHull(largest_try)
        peri = cv.arcLength(hull, True)

        if debug:
            image_hull = img.copy()
            convex_hull = cv.drawContours(image_hull, [hull], -1, (0, 0, 255), 5)

        approx = None
        for eps in np.linspace(0.02, 0.06, 10):
            candidate = cv.approxPolyDP(hull, eps * peri, True)
            if len(candidate) == 4:
                approx = candidate
                if debug:
                    paper_image = img.copy()
                    paper_display = cv.drawContours(paper_image, [approx], -1, (0, 255, 0), 10)
                break

        # must have 4 points
        if approx is None:
            continue

        pts_try = approx.reshape(4, 2).astype("float32")

        # ---------- order points ----------
        pts_try = order_points(pts_try)

        if debug:
            points_paper = img.copy()
            for (x, y) in pts_try:
                cv.circle(points_paper, (int(x), int(y)), 30, (0, 0, 255), -1)

        # ---------- compute width & height ----------
        widthA = np.linalg.norm(pts_try[2] - pts_try[3])
        widthB = np.linalg.norm(pts_try[1] - pts_try[0])
        maxWidth = int(max(widthA, widthB))
        print("this are the points:\n", pts_try)

        heightA = np.linalg.norm(pts_try[1] - pts_try[2])
        heightB = np.linalg.norm(pts_try[0] - pts_try[3])
        maxHeight = int(max(heightA, heightB))

        # no crash, samo reject  kernel
        if maxHeight == 0 or maxWidth == 0:
            continue

        # ---------- ACCEPT RESULT ----------
        contours = contours_try
        largest = largest_try
        used_edges = temp_edges
        edges = temp_edges
        pts = pts_try

        break

    # final validation after retry loop
    if contours is None or largest is None or pts is None:
        if verify:
            raise Exception("Invalid detected paper dimensions (zero width/height). No 4 points detected. Default to Manual Crop")
        else:
            raise Exception("Invalid detected paper dimensions (zero width/height). No 4 points detected. ")

    # ---------- VERIFY MODE ----------
    # When verify=True:
    # The function stops after document detection and returns a preview
    # image with the detected corner points drawn on it.
    #
    # This allows the user to visually confirm that the detected paper
    # region is correct before OCR/perspective transformation happens.
    #
    # After confirmation, the same function is called again WITHOUT
    # verify=True, causing the function to continue normally through:
    # perspective transform -> OCR extraction -> final result.
    #
    # This avoids duplicating half the detection pipeline in a separate
    # verification function and keeps all detection logic centralized.
    if verify:
        if not debug:
            points_paper = img.copy()
            for (x, y) in pts:
                cv.circle(points_paper, (int(x), int(y)), 30, (0, 0, 255), -1)
        path = create_path(verify_path, "verify.jpg")
        cv.imwrite(path, points_paper)
        print(path, " AND THE POINTS:", pts)
        return (path, pts)

    if debug:
        image_largest_contour = img.copy()
        largest_contour = cv.drawContours(image_largest_contour, [largest], -1, (0, 255, 255), 5)
    # ---------- destination points ----------
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    # ---------- validate detected paper ----------

    imgHeight, imgWidth = img.shape[:2]
    imgArea = imgWidth * imgHeight

    paperArea = maxWidth * maxHeight
    coverage = paperArea / imgArea

    # A4 aspect ratio:
    # portrait  ≈ 0.707
    # landscape ≈ 1.414
    aspectRatio = maxWidth / maxHeight

    valid_aspect_ratio = (
            0.65 <= aspectRatio <= 0.80 or
            1.20 <= aspectRatio <= 1.50
    )

    valid_size = (
            maxWidth > 100 and
            maxHeight > 100
    )

    if debug:
        print("\n---------- Detection Validation ----------")
        print(f"Image Size: {imgWidth}x{imgHeight}")
        print(f"Paper Size: {maxWidth}x{maxHeight}")
        print(f"Coverage Ratio: {coverage:.2f}")
        print(f"Aspect Ratio: {aspectRatio:.2f}")
        print(f"Aspect Valid: {valid_aspect_ratio}")
        print(f"Size Valid: {valid_size}")

    # ---------- invalid detections ----------

    if not valid_size:
        raise Exception(
            "Detected contour dimensions are unrealistically small."
        )

    if not valid_aspect_ratio:
        raise Exception(
            "Detected contour does not resemble paper proportions."
        )

    # ---------- decision logic ----------

    # CASE 1:
    # contour is tiny compared to image
    # likely wrong contour / missed paper

    if coverage < 0.20:

        raise Exception(
            "Detected paper is too small or contour detection failed."
        )

    # CASE 2:
    # paper almost fully fills image
    # likely already perfectly aligned

    elif coverage >= 0.90:

        if debug:
            print("Paper already fills frame -> skipping perspective transform")

        warped = orig.copy()

    # CASE 3:
    # normal document detection
    # apply perspective correction

    else:

        if debug:
            print("Applying perspective transform")

        # ---------- perspective transform ----------
        M = cv.getPerspectiveTransform(pts, dst)

        warped = cv.warpPerspective(orig,M,(maxWidth, maxHeight)
        )
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
    # ---------- RETURN GREYSCALE WARPED IMAGE ----------
    gray_warped = warped.copy()
    gray_warped = cv.cvtColor(gray_warped, cv.COLOR_BGR2GRAY)

    return gray_warped


def warp_perspective_image(selected_image_path, points):
    # ---------- Load Image ----------
    img = cv.imread(selected_image_path)
    if img is None:
        raise Exception("Image could not be loaded")

    orig = img.copy()


    # ---------- Create Numpy Array & Order Points ----------
    points = np.array(points, dtype="float32")
    ordered_points = order_points(points)

    # ---------- compute width & height ----------
    widthA = np.linalg.norm(ordered_points[2] - ordered_points[3])
    widthB = np.linalg.norm(ordered_points[1] - ordered_points[0])
    maxWidth = int(max(widthA, widthB))
    print("this are the points:\n", ordered_points)

    heightA = np.linalg.norm(ordered_points[1] - ordered_points[2])
    heightB = np.linalg.norm(ordered_points[0] - ordered_points[3])
    maxHeight = int(max(heightA, heightB))

    if maxWidth == 0 or maxHeight == 0:
        raise Exception("Invalid warp dimensions")

    # ---------- destination points ----------
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    # ---------- perspective transform ----------
    M = cv.getPerspectiveTransform(ordered_points, dst)

    warped = cv.warpPerspective(orig, M, (maxWidth, maxHeight))
    gray = cv.cvtColor(warped, cv.COLOR_BGR2GRAY)

    print(pt.image_to_string(gray, lang="eng"))

    return gray