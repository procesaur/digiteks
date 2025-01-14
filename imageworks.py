from io import BytesIO
from PIL import Image
from cv2 import cvtColor, resize, threshold, dilate, erode, warpAffine, getRotationMatrix2D, medianBlur, adaptiveThreshold, GaussianBlur, bilateralFilter, filter2D
from cv2 import BORDER_REPLICATE, COLOR_BGR2RGB, COLOR_RGB2BGR, COLOR_BGR2GRAY, THRESH_OTSU, THRESH_BINARY, INTER_CUBIC, ADAPTIVE_THRESH_GAUSSIAN_C
from numpy import ndarray, array as nparray, ones, uint8, max, sum as npsum, arange


def improve_image(image):
    img = convert_from_image_to_cv2(image)
    img = resize_img(img)
    img = cvtColor(img, COLOR_BGR2GRAY)

    img = blur_img(img)
    img = erode_img(img)
    img = correct_skew(img)

    return convert_from_cv2_to_image(img)


def img2bytes(img):
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def bytes2img(img):
    return Image.open(BytesIO(img))

def sharpen_img(img):
    sharpen_kernel = nparray([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpen = filter2D(img, -1, sharpen_kernel)
    return sharpen


def resize_img(img):
    #img = resize(img, (0, 0), fx=2, fy=2)
    img = resize(img, None, fx=1.2, fy=1.2, interpolation=INTER_CUBIC)
    return img


def erode_img(img):
    kernel = ones((1, 1), uint8)

    img = erode(img, kernel, iterations=1)
    img = dilate(img, kernel, iterations=2)
    return img


def blur_img(img):

    img = threshold(bilateralFilter(img, 5, 75, 75), 0, 255, THRESH_BINARY + THRESH_OTSU)[1]
    # img = adaptiveThreshold(bilateralFilter(img, 5, 100, 100), 255, ADAPTIVE_THRESH_GAUSSIAN_C, THRESH_BINARY, 31, 2)
    # img = threshold(img, 0, 255, THRESH_BINARY + THRESH_OTSU)[1]

    return img


def convert_from_cv2_to_image(img: ndarray) -> Image:
    return Image.fromarray(cvtColor(img, COLOR_BGR2RGB))


def convert_from_image_to_cv2(img: Image) -> ndarray:
    return cvtColor(nparray(img), COLOR_RGB2BGR)


def correct_skew(image, delta=1, limit=8):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    def determine_score(image, angle):
        M = getRotationMatrix2D(center, angle, 1.0)
        data = warpAffine(image, M, (w, h), flags=INTER_CUBIC, borderMode=BORDER_REPLICATE)

        histogram = npsum(data, axis=1, dtype=float)
        score = npsum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return score

    scores = []
    angles = arange(-limit, limit + delta, delta)
    for angle in angles:
        scores.append(determine_score(image, angle))

    best_angle = angles[scores.index(max(scores))]

    M = getRotationMatrix2D(center, best_angle, 1.0)
    rotated = warpAffine(image, M, (w, h), flags=INTER_CUBIC, borderMode=BORDER_REPLICATE)

    return rotated