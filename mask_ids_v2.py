import os

import cv2
import numpy as np
# import paddleocr
from paddleocr import PaddleOCR,draw_ocr

import re
from config import config_dict
from utils_v2 import encrypt_v4,encrypt_v3
do_normalization = True
do_nltk = False

if do_nltk:
    import nltk  #for removing non english words

    try:
        words = set(nltk.corpus.words.words())  # create corpus from words later used for identifying
    except:
        nltk.download('words')
        words = set(nltk.corpus.words.words())

# reader = easyocr.Reader(['en', ], gpu=False)
reader = PaddleOCR(use_angle_cls=True, lang='en', ocr_version='PP-OCRv4', use_space_char=True,show_log = False)
face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def nor_images(image):
    img = get_grayscale(image)

    img = normalized_image(img)

    kernel = np.ones((1, 1), np.uint8)
    img = cv2.erode(img, kernel, iterations=3)

    return img

def normalized_image(img):
    norm_img = np.zeros((img.shape[0], img.shape[1]))
    img = cv2.normalize(img, norm_img, 0, 255, cv2.NORM_MINMAX)
    return img


def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def find_pattern(text):

    redaction_patterns = [

       
        [r"\b\d{4}\s*\d{4}\s*\d{4}\b", "aadhar"],  # for aadhar
        [r"[A-Z]{5}[0-9]{4}[A-Z]{1}", "pan"],  #for pan
        [r"^(([A-Z]{2}[0-9]{2})([A-Z]{2}-[0-9]{2}))((19|20)[0-9][0-9])[0-9]{7}$", "dl"],  #for Driving License
        [r"^[A-Z]{1}[0-9]{7}$", "passport"],  #for passport
        # [r"^[A-PR-WY-Z][1-9]\\d\\s?\\d{4}[1-9]$", "passport"],  #for passport
        [r"^[A-Z]{1}[0-9]{7}", "passport2"],
        [r"^([a-zA-Z]{2}[0-9]{2})([0-9]{11})$", "dl"],
        [r"(([a-zA-Z]{2}[0-9]{2})|([A-Z]{2}-[0-9]{2}))((19|20)[0-9 ][0-9])[0-9]{7}$", "dl"],
        [r"^[A-Z]{3}[0-9]{7}$", "voter"],
        [r"^\d{4}\s?\d{4}\s?\d{4}$","aadhar"],
        [r"\b\d{10}\b", "mobile"],
        [r"\b(0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])[-/](19\d\d|20\d\d)\b", "date"],  #pattern for date
        [r"^[0-9]{1,2}\/[0-9]{1,2}\/[0-9]{4}$", "date"],
        [r"^[0-9]{1,2}\-[0-9]{1,2}\-[0-9]{4}$", "date"],
        [r"\d{1,2}\/\d{1,2}\/\d{2,4}", "date"],
        [r"\d{1,2}1\d{1,2}1\d{2,4}", "date"],
        [r"(?i)[Aa][adeoc]{2}ress", "address"],
        [r'[1,2]\d{3}', "year"],
        [r"^(([A-Z]{1}[0-9]{2})([A-Z]{2}-[0-9]{2}))((19|20)[0-9][0-9])[0-9]{7}$", "dl"],
        [r"^([a-zA-Z]{1}[0-9]{13})$", "dl"],
        # [r'\b\d{4}\b', "aadhar"],
        # [r'\b\d{8}\b', "aadhar"],
    ]
    text2 = text.replace(" ", '')
    for pattern in redaction_patterns:
        val = re.findall(pattern[0], text)
        if val and len(val) > 0:
            return val, pattern[1]
        val = re.findall(pattern[0], text2)
        if val and len(val) > 0:
            return val, pattern[1]
        val = re.findall(pattern[0], text.lower())
        if val and len(val) > 0:
            return val, pattern[1]
        val = re.findall(pattern[0], text2.lower())
        if val and len(val) > 0:
            return val, pattern[1]
    return None, None


def check_special(text):
    regex = re.compile('[@!#$%^&*()<>?}{~]')

    if (regex.search(text) == None):
        return False

    else:
        return True


def perform_tilt_correction(image):
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gaussian_blur = cv2.GaussianBlur(gray_img, (7, 7), 2)
    sharpened_image = cv2.addWeighted(gray_img, 1.5, gaussian_blur, -0.5, 0)

    edges = cv2.Canny(sharpened_image, 50, 150, apertureSize=3)
    pts = np.argwhere(edges > 0)
    y1, x1 = pts.min(axis=0)
    y2, x2 = pts.max(axis=0)

    cropped = image[y1:y2, x1:x2]


    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

    if lines is not None and len(lines) > 0:
        rho, theta = lines[0][0]
        angle_deg = theta * (180 / np.pi)

        top_edge_angle = 90  # The top horizontal edge is horizontal (90 degrees)
        angle_between_top_edge_and_text = (top_edge_angle - angle_deg)
        if -15 < angle_between_top_edge_and_text < 15:
            rotation_angle_degrees = 0
        elif 75 < angle_between_top_edge_and_text < 105:
            rotation_angle_degrees = 0
        else:
            rotation_angle_degrees = angle_between_top_edge_and_text
        height, width = image.shape[:2]

        rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), -1 * rotation_angle_degrees, 1)

        rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))
        gray_image = cv2.cvtColor(rotated_image, cv2.COLOR_BGR2GRAY)

        rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))

        return rotated_image
    else:
        return image



font = cv2.FONT_HERSHEY_SIMPLEX


def rotate(image, angle, center=None, scale=1.0):
    (h, w) = image.shape[:2]

    if center is None:
        center = (w / 2, h / 2)

    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated = cv2.warpAffine(image, M, (w, h))

    return rotated


def improve_resolution(image):
    gaussian_blur = cv2.GaussianBlur(image, (7, 7), 2)
    sharpened_image = cv2.addWeighted(image, 1.5, gaussian_blur, -0.5, 0)
    return sharpened_image

def is_unsupported_doc(text):
    unsupported_keyword_list = ['gst','agreement','bank','certificate','bill','leave','index']
    for keyword in unsupported_keyword_list:
        if keyword in text.lower():
            return True
    return False
def is_valid_doc(text):
    
    valid_keyword_list = ["election","uidal", "uidai","income","driv","licencing","government of india",'unique']
    for keyword in valid_keyword_list:
        if keyword in text.lower():
            return True
    return False

def mask_maker_v2(image,key):
    valid_doc_list = ['aadhar','pan','dl','passport','voter']
    valid_doc = False
    clear_img = False
    document_type = 'unsupported'
    #document_path = IMAGE_PATH
    image_org = image.copy()
    try:
        image = improve_resolution(image)
    except:
        print("Some Issue while enhancing image resolution continuing with original images")
        image = image_org
    spacer = 100
    try:
        image = perform_tilt_correction(image)
    except:
        print("tilt correction failed , continuing with original images")
        image = image_org

    # img = image
    # original_image = image.copy()
    # img2 = image.copy()

    face = face_classifier.detectMultiScale(
        image, scaleFactor=1.07, minNeighbors=3, minSize=(50, 50)
    )

    try:
        if do_normalization:
            normalized_image = nor_images(image)
        else:
            normalized_image = image
    except:
         normalized_image = image


    result = reader.ocr(normalized_image)
 
    if len(result) == 0 or result[0] is None:
        # cv2.imwrite('unsupported/' + img_name + '_uns.'+ ext, image_org)
        
        return  200,document_type,"picture quality is not up to mark", image_org


    for (x, y, w, h) in face:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)
    for detection in result[0]:

        top_left = [int(detection[0][0][0]), int(detection[0][0][1])]
        bottom_right = [int(detection[0][2][0]), int(detection[0][2][1])]
        bottom_right[1] = top_left[1] + max(40,bottom_right[1]-top_left[1])
        text = detection[1][0]
        
        
        if is_unsupported_doc(text):
            valid_doc = False
            # cv2.imwrite('unsupported/' + img_name + '_uns.'+ ext, image_org)
            
            return 200,document_type, "document not in the list of supported documents", image_org

        
        if len(text) < 4 or "india" in text.lower() or " of " in text.lower():
            continue

        # text_lower= text.lower()
     
        if is_valid_doc(text):
            valid_doc = valid_doc or True

        spacer += 20

        pattern, type_of_data = find_pattern(text)

        if type_of_data == 'address':
            if len(text) <20 :
                bottom_right[0] = top_left[0] + 5 * (bottom_right[0] - top_left[0])
            bottom_right[1] = top_left[1] + 5 * (bottom_right[1] - top_left[1])
            image = cv2.rectangle(image, top_left, bottom_right , (0, 0, 0), -1)
        if pattern and len(pattern) > 0:
          
            text = pattern
            if type_of_data == 'aadhar':
                aadhar = True
                bottom_right[0] = top_left[0] + 9 *(bottom_right[0] - top_left[0]) //12
            elif type_of_data == 'pan' or type_of_data == 'voter':
                aadhar = True
                bottom_right[0] = top_left[0] + 7 *(bottom_right[0] - top_left[0]) //10
            elif type_of_data == 'passport':
                aadhar = True
                bottom_right[0] = top_left[0] + 5 *(bottom_right[0] - top_left[0]) //8

            elif type_of_data == 'dl':
                aadhar = True
                bottom_right[0] = top_left[0] + 17 *(bottom_right[0] - top_left[0]) //20
            elif type_of_data in valid_doc_list:
                bottom_right[0] = top_left[0] + 6 *(bottom_right[0] - top_left[0]) //8
            image = cv2.rectangle(image, top_left, bottom_right, (0, 0, 0), -1)
          
        if type_of_data in valid_doc_list:
            document_type = type_of_data
            clear_img = clear_img or True
            
        
    if clear_img:
        
        return 200,document_type,"Processed succesfully",image  #returns the masked image   

    elif valid_doc and not clear_img:
    
        return 200,document_type, "picture quality is not up to mark", image_org
    
   
    return 200,document_type,"document not in the list of supported documents",image_org
    