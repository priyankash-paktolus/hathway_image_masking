import os
import portalocker
import base64
import cv2
import time,jwt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import json
from cryptography.hazmat.backends import default_backend
import os
from config import config_dict

from PIL import Image, ImageDraw, ImageFont

def add_watermark(image,watermark_texts):
    color_converted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    source_image = Image.fromarray(color_converted).convert('RGBA')

    # Create a draw object for the original image
    draw = ImageDraw.Draw(source_image)

    # Set the transparency level and watermark color
    alpha = 0.8
    watermark_color = (255, 255, 120)

    # Load the font
    font_size = source_image.height // 65
    font = ImageFont.truetype("Arial.ttf", font_size)

    # Create a blank image for the watermark text
    watermark_image = Image.new("RGBA", source_image.size, (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(watermark_image)
    
    # Unpack watermark texts
    watermark1, watermark2, watermark3 = watermark_texts
    
    # Calculate the bounding box for the watermark text
    watermark1_bbox = watermark_draw.textbbox((0, 0), watermark1, font=font)
    watermark2_bbox = watermark_draw.textbbox((0, 0), watermark2, font=font)
    watermark3_bbox = watermark_draw.textbbox((0, 0), watermark3, font=font)
    
    # Get the maximum height of the watermark texts
    max_height = max(watermark1_bbox[3], watermark2_bbox[3], watermark3_bbox[3])
    
    # Calculate center coordinates for the watermark
    center_x = (source_image.width - watermark1_bbox[2]) // 2
    center_y = 10 + (source_image.height - ( max_height)) // 2  # Adjusted for vertical spacing

    # Draw the watermark text onto the blank image
    watermark_draw.text((center_x, center_y), watermark1, fill=(watermark_color[0], watermark_color[1], watermark_color[2], int(255 * alpha)), font=font)
    watermark_draw.text((center_x, center_y + max_height), watermark2, fill=(watermark_color[0], watermark_color[1], watermark_color[2], int(255 * alpha)), font=font)
    watermark_draw.text((center_x, center_y + 2 * max_height), watermark3, fill=(watermark_color[0], watermark_color[1], watermark_color[2], int(255 * alpha)), font=font)

    # Rotate the watermark image if needed
    watermark_image = watermark_image.rotate(-420, expand=True)

    # Paste the watermark onto the original image
    source_image.paste(watermark_image, (0, 0), watermark_image)

    # Save the resulting image
    return source_image

def add_watermark2(image, watermark_texts):
    # Open the image
    color_coverted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(color_coverted)
    image = image.convert('RGBA')

    # Create a blank image for the text with a transparent background
    txt_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))

    # Choose a font and size
    #font = ImageFont.load_default()  # You can load your preferred font here
    font_path = 'Arial.ttf'  # Replace with your font file path
    font_size = max(image.height,image.width,200) // 65  # Specify the desired font size
    font = ImageFont.truetype(font_path, font_size)
    # Create a drawing context
    draw = ImageDraw.Draw(txt_layer)

    # Calculate positioning and inclination
    width, height = image.size
    margin = 10  # Margin from the image border
    text_height = sum([draw.textbbox((0, 0), text, font=font)[3] - draw.textbbox((0, 0), text, font=font)[1] for text in watermark_texts])

    x = (width - text_height)//2 + margin
    y = margin + (height - text_height) // 2  # Start watermarking from one-third of the image height

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
def encrypt_v4(img,key):

    # Generate a random IV (Initialization Vector)
    key = base64.b64decode(key)
    #print(key)
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

   # print("reading image file done")
    # Pad the data to be a multiple of the block size (16 bytes for AES)
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    # Encrypt the data
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    # encrypted_image_name = f"{img_name}.enc"
    # encrypted_filename = f"{os.path.join(config_dict["base_dir"],config_dict["processed_dir"],config_dict["enc_image_dir"],os.path.basename(os.path.dirname(img_path)),encrypted_image_name)}"
    # try:
    #     with open(encrypted_filename, 'wb') as f:
    #         f.write(iv + encrypted_data)
    # except Exception as e:
    #     print("not able to write image due to some error" )
   # print(iv)
   # print(encrypted_data[:20])
    return iv + encrypted_data

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
        #print('Encryption Done...')


    except Exception:
        print('Error caught : ', Exception.__name__)



def decrypt_v4(encrypted_data,key ):
    try:
        iv = encrypted_data[:16]
 #byte_data = string.encode('utf-8')
        encrypted_data = encrypted_data[16:]
        # Create a cipher object

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
       # print("iv",iv)
       # print("enc data",encrypted_data[:20])
       # print(4)
        # Decrypt the data
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
       # print(5)
        # Unpad the data
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
       # print(6)
        data = unpadder.update(padded_data) + unpadder.finalize()
       # print(7)
        return data
    #removed file saving logic
        # output_filename = path.replace('.enc', '')
        # output_filename = output_filename.replace('encrypted', 'decrypted')
        # # Write the decrypted data to the output file
        # with open(output_filename, 'wb') as f:
        #     f.write(data)
        #     return data

    except Exception:
       # print('Error caught : ', Exception.__name__)
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
        fin = open(path, 'wb')

        # writing decryption data in image
        fin.write(image)
        fin.close()
        return path

    except Exception:
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
tokens_file_path = 'tokens_data.json'

def read_tokens_from_file():
    if os.path.exists(tokens_file_path):
        with open(tokens_file_path,'r') as f:
            return json.load(f)
    return {}

def write_tokens_to_file(tokens_db):
    with open(tokens_file_path,'w') as f:
        json.dump(tokens_db,f)



def generate_token(key="try"):
    # Expiration time for 24 hours
    expiration_time = time.time() + 86400
    
    # Payload to encode into the token
    payload = {
        'exp': expiration_time
    }
    
    # Encode the payload into a JWT token
    token = jwt.encode(payload, key, algorithm='HS256')

    # Store token with expiration time in in-memory DB (This would be a database in a real app)
    tokens_db = read_tokens_from_file()
    tokens_db[token] = expiration_time 
    with open(tokens_file_path,'r+') as f:
        portalocker.lock(f,portalocker.LOCK_EX)
        write_tokens_to_file(tokens_db)
        portalocker.unlock(f)


    return token

def verify_token(token,key="try"):
   
    try:
        # Decode the token using the secret key
        decoded = jwt.decode(token, key, algorithms=['HS256'])
        
        tokens_db = read_tokens_from_file()
        if token not in tokens_db:
            return "Token not found"
        # Check if the token is in the "database" and not expired
        # Check if token has expired
        if time.time() > tokens_db[token]:
            return "Token has expired"
        
        return "Token is valid"
    
    except :
        return "Invalid token"



