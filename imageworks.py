from io import BytesIO
from PIL import Image
from cv2 import cvtColor, resize, threshold, dilate, erode, warpAffine, getRotationMatrix2D, bilateralFilter
from cv2 import BORDER_REPLICATE, COLOR_BGR2RGB, COLOR_RGB2BGR, COLOR_BGR2GRAY, THRESH_OTSU, THRESH_BINARY, INTER_CUBIC, INTER_AREA
from numpy import ndarray, array as nparray, ones, uint8, max, sum as npsum, arange
from pdf2image import convert_from_bytes
from helper import cpus, pool, read_zip, decode_image, encode_image


def improve_image(img):
    processing = [
        convert_from_image_to_cv2,
        img_color_convert,
        #resize_img,
        blur_img,
        erode_img,
        #resize_img,
        correct_skew,
        convert_from_cv2_to_image
    ] 
    
    for x in processing:
        img = x(img)

    return img2bytes(img)


def img_color_convert(img):
    return cvtColor(img, COLOR_BGR2GRAY)

def img2bytes(img):
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG', color=2)
    return img_byte_arr.getvalue()


def bytes2img(img):
    return Image.open(BytesIO(img))



def resize_img(img, x=2, y=2, interpolation=INTER_CUBIC):
    #img = resize(img, (0, 0), fx=2, fy=2)
    img = resize(img, None, fx=x, fy=y, interpolation=interpolation)
    return img


def erode_img(img):
    kernel = ones((1, 1), uint8)

    img = dilate(img, kernel, iterations=2)
    img = erode(img, kernel, iterations=2)

    return img


def blur_img(img):
    img = threshold(bilateralFilter(img, 5, 75, 75), 0, 255, THRESH_BINARY + THRESH_OTSU)[1]
    return img


def convert_from_cv2_to_image(img: ndarray) -> Image:
    return Image.fromarray(cvtColor(img, COLOR_BGR2RGB))


def convert_from_image_to_cv2(img: Image) -> ndarray:
    return cvtColor(nparray(img), COLOR_RGB2BGR)


def correct_skew(image, delta=0.3, limit=9):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    def determine_score(angle):
        M = getRotationMatrix2D(center, angle, 1.0)
        data = warpAffine(image, M, (w, h), flags=INTER_CUBIC, borderMode=BORDER_REPLICATE)

        histogram = npsum(data, axis=1, dtype=float)
        score = npsum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return score

    angles = arange(-limit, limit + delta, delta)
    scores = [determine_score(angle) for angle in angles]

    best_angle = angles[scores.index(max(scores))]
    M = getRotationMatrix2D(center, best_angle, 1.0)
    rotated = warpAffine(image, M, (w, h), flags=INTER_CUBIC, borderMode=BORDER_REPLICATE)
    return rotated


def pdf_to_images(file_bytes, img_down=False):
    images = convert_from_bytes(file_bytes, dpi=300, thread_count=cpus)
    if img_down:
        images_improved = pool.map(improve_image, images)
        return [(img2bytes(a), b) for a, b in zip(images, images_improved)]
    return [img2bytes(a) for a in images]


def image_zip_to_images(file):
    images = read_zip(file)
    images = [bytes2img(img) for img in images]
    images_improved = pool.map(improve_image, images)
    return images, images_improved


def crop_image(base64_image, x1, y1, x2, y2):
    image_data = decode_image(base64_image)
    image = Image.open(BytesIO(image_data))
    
    cropped_image = image.crop((x1, y1, x2, y2))
    
    buffered = BytesIO()
    cropped_image.save(buffered, format="JPEG")

    return encode_image(buffered.getvalue())