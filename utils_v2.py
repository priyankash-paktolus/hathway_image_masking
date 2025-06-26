import os

import base64
import cv2
from PIL import Image, ImageDraw, ImageFont

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

from cryptography.hazmat.backends import default_backend
import os
from config import config_dict


def get_draft_id(path):
    filename = os.path.basename(path)
    return filename.split("_")[0]
    # return os.path.basename(path)
def add_watermark2(image, watermark_texts):
    # Open the image
    color_coverted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(color_coverted)
    image = image.convert('RGBA')
    # Create a blank image for the text with a transparent background
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
    # Choose a font and size
    #font = ImageFont.load_default()  # You can load your preferred font here
    font_path = '/reports/Image_masking_test_api/image_mask/Arial.ttf'  # Replace with your font file path
    font_size = max(image.height,image.width,200) // 65  # Specify the desired font size
    font = ImageFont.truetype(font_path, font_size)
    # Create a drawing context
    draw = ImageDraw.Draw(txt_layer)
    # Calculate positioning and inclination
    width, height = image.size
    margin = 10  # Margin from the image border
    text_height = sum([draw.textbbox((0, 0), text, font=font)[3] - draw.textbbox((0, 0), text, font=font)[1] for text in watermark_texts])
    x = (width - text_height)//5 + margin
    y = margin + (height - text_height) // 2
  # Start watermarking from one-third of the image heigh
    # Draw each line of text
    for i, text in enumerate(watermark_texts):
        draw.text((x, y + i * 30), text, font=font, fill=(255, 255, 120, 255))
    # Rotate the text layer to create the inclination
    rotated_txt_layer = txt_layer.rotate(-60, expand=1)
    # Create a new layer of the same size as the original image
    txt_layer_resized = Image.new("RGBA", image.size, (255, 255, 255, 0))
    # Paste the rotated text layer back into the resized transparent layer, centered
    txt_layer_resized.paste(rotated_txt_layer, (int((width - rotated_txt_layer.width) / 2),
                                                int((height - rotated_txt_layer.height) / 2)), rotated_txt_layer)
    # Combine the original image with the resized text layer
    watermarked = Image.alpha_composite(image, txt_layer_resized)
    # print("*" *10)
    # print(watermarked)
    return watermarked.convert("RGB")





# Key derivation function
# def derive_key(password: bytes, salt: bytes) -> bytes:
#     kdf = PBKDF2HMAC(
#         algorithm=hashes.SHA256(),
#         length=32,
#         salt=salt,
#         iterations=100000,
#         backend=default_backend()
#     )
#     return kdf.derive(password)


def encrypt_v4(img,img_path,img_name,ext,key ):
 #   print(key)
#    print("image_path"+img_path)
    # Generate a random IV (Initialization Vector)
    key = base64.b64decode(key)
    iv = os.urandom(16)
    
    # Create a cipher object
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    try:
        encryptor = cipher.encryptor()
    except Exception:
        print('Error caught : ', Exception.__name__)
  #  print("starting reAding file")
    # Open the input file and create an output file
    # try:
    #     with open(img_path, 'rb') as f:
    #         data = f.read()
    # except Exception as e:
    #     print("error in loading the image for encryption")
    data = img

    # Pad the data to be a multiple of the block size (16 bytes for AES)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    # Encrypt the data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    encrypted_image_name = f"{img_name}.{ext}.enc"
    encrypted_filename = f"{os.path.join(config_dict["base_dir"],config_dict["op_dir"],config_dict["enc_image_dir"],os.path.basename(os.path.dirname(img_path)),encrypted_image_name)}"
    try:
        with open(encrypted_filename, 'wb') as f:
            f.write(iv + encrypted_data)
    except Exception as e:
        print("not able to write image due to some error" )

    return encrypted_filename



def encrypt_v3(img_path,img_name):
    # try block to handle exception
    try:

        key = 34
     

        # open file for reading purpose
        fin = open(img_path, 'rb')

        # storing image data in variable "image"
        image = fin.read()
        fin.close()

        # converting image into byte array to
        # perform encryption easily on numeric data
        image = bytearray(image)

        # performing XOR operation on each value of bytearray
        for index, values in enumerate(image):
            image[index] = values ^ key

        encrypted_filename = f"encrypted/{img_name}.enc"
        # opening file for writing purpose
        fin = open(encrypted_filename, 'wb')

        # writing encrypted data in image
        fin.write(image)
        fin.close()
        print('Encryption Done...')


    except Exception:
        print('Error caught : ', Exception.__name__)


# def encrypt_v2(img, img_name):
#     height, width, _ = img.shape
#     img_bytes = img.tobytes()

#     # Key and salt
#     password = b'secret_password'  # This should be securely managed
#     salt = os.urandom(16)
#     key = derive_key(password, salt)

#     padder = padding.PKCS7(algorithms.AES.block_size).padder()
#     padded_data = padder.update(img_bytes) + padder.finalize()

#     # AES encryption
#     iv = os.urandom(16)
#     cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
#     encryptor = cipher.encryptor()
#     encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

#     encrypted_filename = f"encrypted/{img_name}.enc"
#     with open(encrypted_filename, 'wb') as f:
#         f.write(salt + iv + height.to_bytes(4, byteorder='big') + width.to_bytes(4, byteorder='big') + encrypted_data)

#     return encrypted_filename

def decrypt_v4(encrypted_image_path,key ):
    try:
        # take path of image as a input
        path = encrypted_image_path
        with open(encrypted_image_path, 'rb') as f:
            iv = f.read(16)
            encrypted_data = f.read()
        # Create a cipher object
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the data
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Unpad the data
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        # print(data)
        return data
    #removed file saving logic
        # output_filename = path.replace('.enc', '')
        # output_filename = output_filename.replace('encrypted', 'decrypted')
        # # Write the decrypted data to the output file
        # with open(output_filename, 'wb') as f:
        #     f.write(data)
        #     return data

    except Exception:
        print('Error caught : ', Exception.__name__)
        return "can not process image"



def decrypt_v3(encrypted_image_path):
    try:
        # take path of image as a input
        path = encrypted_image_path

        # taking decryption key as input
        key = 34

        # open file for reading purpose
        fin = open(path, 'rb')

        # storing image data in variable "image"
        image = fin.read()
        fin.close()

        # converting image into byte array to perform decryption easily on numeric data
        image = bytearray(image)

        # performing XOR operation on each value of bytearray
        for index, values in enumerate(image):
            image[index] = values ^ key

        # opening file for writing purpose
        path = path.replace('.enc', '')
        print(path)
        fin = open(path, 'wb')

        # writing decryption data in image
        fin.write(image)
        fin.close()
        print('Decryption Done...')
        return path

    except Exception:
        print('Error caught : ', Exception.__name__)
        return "can not process image"

# def decrypt_v2(encrypted_image_path, output_filename):
#     with open(encrypted_image_path, 'rb') as f:
#         salt = f.read(16)
#         iv = f.read(16)
#         height_bytes = f.read(4)
#         width_bytes = f.read(4)
#         encrypted_data = f.read()

#     height = int.from_bytes(height_bytes, byteorder='big')
#     width = int.from_bytes(width_bytes, byteorder='big')

#     password = b'secret_password'
#     key = derive_key(password, salt)

#     # AES decryption
#     cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
#     decryptor = cipher.decryptor()
#     decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

#     unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
#     unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()

#     img = np.frombuffer(unpadded_data, dtype=np.uint8).reshape((height, width, 3))

#     cv2.imwrite(output_filename, img)
#     return img
