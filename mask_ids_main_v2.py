from flask import Flask, request, jsonify,send_file
import os
import time
from mask_ids import mask_maker_v2
import csv
from utils import decrypt_v4,encrypt_v4,add_watermark2,generate_token,verify_token
from config import config_dict
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2400 * 1024 * 1024

app.config['SECRET_KEY'] = 'your_secret_key_here'
# A simple in-memory storage for the tokens (in a real app, use a database)
tokens_db = {}
from io import BytesIO
import base64
#testing start
import cv2
import numpy as np
from io import BytesIO


@app.route('/mask_maker', methods=['POST'])
def mask_ids():
    data = request.json
    if 'token' not in data :
        return jsonify({'error': 'Token are required'}), 400
    token = data['token']
    token_verification_status = verify_token(token)
    if token_verification_status == "Token not found":
        return jsonify({'error':'Invalid token'}),400
    
    if token_verification_status == "Token has expired":
        return jsonify({'error':'Token has expired'}),400
    
    if token_verification_status == "Invalid token":
        return jsonify({'error':'Invalid token'}),400
    
    if token_verification_status == 'Token is valid':
        if 'ImageInfo' not in data:
            return jsonify({'error': 'ImageInfo are required'}), 400
        if 'watermarkInfo' not in data:
            return jsonify({'error': 'watermarkInfo are required'}), 400
        if 'AccountId' not in data :
            return jsonify({'error': 'AccountId is missing'}), 400

        water_mark_data = data["watermarkInfo"]
        watermark_text = [f"Lat {water_mark_data['latitude']} | Long {water_mark_data['longitude']} | accountNo {water_mark_data['accountNo']}" ,
        f"POS Name {water_mark_data['posName']} | POS Code {water_mark_data['posCode']} ",
        f"Date and Time {water_mark_data['dateTimeTs']} " 
        ]
        # Decode the image from base64
        response_dict = {"AccountId": data["AccountId"],
        "MaskImageInfo": [],
        "EncImageInfo": []
        }
        
        for i in data["ImageInfo"]:
            img_name = i["Target File"]
            img = i["image"]
            image_data = base64.b64decode(img)  # Handle data URL format
            image_array = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            buffered = BytesIO()
            org_buffered = BytesIO()
            key = "7utxcIOCk+uLPbgRl6d2/xIqbXJ65HX9I+HfptVVcHM="
            processed_image = mask_maker_v2(image_array,key)
            water_marked_image = add_watermark2(processed_image,watermark_text) 
            water_marked_image.save(buffered, format="JPEG")
            response_dict['MaskImageInfo'].append({"DocType": i[ "DocType"],"Target File": img_name,"image":base64.b64encode(buffered.getvalue()).decode('utf-8')
            })
            # response_dict[f"mask_{img_name}"] = base64.b64encode(buffered.getvalue()).decode('utf-8')
            water_marked_image = add_watermark2(image_array,watermark_text) 
            water_marked_image.save(org_buffered, format="JPEG")
            encoded_image = base64.b64encode(encrypt_v4(org_buffered.getvalue(),key)).decode('utf-8')
            response_dict['EncImageInfo'].append({"DocType": i["DocType"],"Target File": img_name,"image":encoded_image
            })
            # encoded_image = base64.b64encode(encrypt_v4(image_data,key)).decode('utf-8')
            # response_dict[f"enc_{img_name}"] = encoded_image

        return jsonify(response_dict),200
    return jsonify({'error':'Something Went Wrong while fullfilling your request'}),500



@app.route("/")
def hello():
    return "<h1 style = 'color:green'>Hello There! image masking is running on this port </h1?"

@app.route('/mask_maker_v2', methods=['POST'])
def apply_mask_to_folder():
    # auth_header = request.headers.get('Authorization')
    # if not auth_header or not auth_header.startswith('Bearer '):
    #     return jsonify({'error': 'Missing or invalid API key'}), 401

    # api_key = auth_header.split()[1]  # Extract API key from header
    # if api_key != API_KEY:
    #     return jsonify({'error': 'Unauthorized'}), 403
    if 'images' not in request.files:
        return jsonify({'error': 'No images found'}), 400

    images_folder = request.files.getlist('images')

    images_paths = []
    key = "7utxcIOCk+uLPbgRl6d2/xIqbXJ65HX9I+HfptVVcHM="
    for idx, image_file in enumerate(images_folder):
        # image_file = image_file.rstrip()
        IMAGE_PATH = os.path.join("images", image_file.filename)
        images_paths.append(IMAGE_PATH)

    masked_images_paths = []
    

    for image_path in images_paths:
        masked_image = mask_maker_v2(image_path,key)
        # masked_image_path = f'masked_{image_path}'
        masked_images_paths.append({image_path:masked_image})

    # Specify the CSV file path
    csv_file = f'data_{time.time()}.csv'

    # Open CSV file for writing
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write header (optional for single dictionary)
        writer.writerow(['Key', 'Value'])

        # Write data rows
        for i in masked_images_paths:
            writer.writerow(i.items())

    print(f'CSV file "{csv_file}" has been created successfully.')
    # for image_path in images_paths:
    #     os.remove(image_path)

    return jsonify({'masked_images_paths': masked_images_paths}), 200

@app.route('/decrypt_multi', methods=['POST'])
def decrypt_multiple_image():
    # auth_header = request.headers.get('Authorization')
    # if not auth_header or not auth_header.startswith('Bearer '):
    #     return jsonify({'error': 'Missing or invalid API key'}), 401

    # api_key = auth_header.split()[1]  # Extract API key from header
    # if api_key !=  config_dict['API_KEY']:
    #     return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    if 'token' not in data :
        return jsonify({'error': 'Token are required'}), 400
    token = data['token']
    token_verification_status = verify_token(token)
    if token_verification_status == "Token not found":
        return jsonify({'error':'Invalid token'}),400
    
    if token_verification_status == "Token has expired":
        return jsonify({'error':'Token has expired'}),400
    
    if token_verification_status == "Invalid token":
        return jsonify({'error':'Invalid token'}),400
    
    if token_verification_status == 'Token is valid':
        if 'EncImageInfo' not in data:
            return jsonify({'error': 'No image Data is provided'}), 400
        if 'encryption_key' not in data:
            return jsonify({'error': 'No encryption key provided'}), 400
        
        encryption_key_hex = data['encryption_key']
        # image_data_byte = data['image']
    
        # Convert hex string back to bytes
        try:
            encryption_key = base64.b64decode(encryption_key_hex)
    
        except ValueError:
            return jsonify({'error': 'Invalid encryption key format'}), 400
        response_dict = {"AccountId": data["AccountId"],

        "DecImageInfo": []
        }

        for i in data["EncImageInfo"]:
            img_name = i["Target File"]
            image_data_byte = i["image"]
            try:
                image_data = base64.b64decode(image_data_byte)
                # print(image_data[:20])
            except Exception as e:
                print(e)
                return jsonify({'error': e}), 400
            try:
                path = decrypt_v4(image_data,encryption_key)
                # buffered = BytesIO()
                # path.save(buffered, format="PNG")
                response_dict['DecImageInfo'].append({"DocType": i["DocType"],"Target File": img_name,"image":base64.b64encode(path).decode('utf-8')
                })
                # return jsonify({'image': base64.b64encode(path).decode('utf-8')}), 200
                # print(decrypted_data)
                # return send_file(decrypted_data,mimetype='image/jpeg', as_attachment=True, download_name='decrypted_image.jpg')
            except Exception as e:
                print(e)
                return jsonify({'error': "error while processing file"}), 500
        return jsonify(response_dict),200
    return jsonify({'error':'Something Went Wrong while fullfilling your request'}),500

@app.route('/decrypt', methods=['POST'])
def decrypt_image():
    # auth_header = request.headers.get('Authorization')
    # if not auth_header or not auth_header.startswith('Bearer '):
    #     return jsonify({'error': 'Missing or invalid API key'}), 401

    # api_key = auth_header.split()[1]  # Extract API key from header
    # if api_key !=  config_dict['API_KEY']:
    #     return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    if 'token' not in data :
        return jsonify({'error': 'Token are required'}), 400
    token = data['token']
    token_verification_status = verify_token(token)
    if token_verification_status == "Token not found":
        return jsonify({'error':'Invalid token'}),400
    
    if token_verification_status == "Token has expired":
        return jsonify({'error':'Token has expired'}),400
    
    if token_verification_status == "Invalid token":
        return jsonify({'error':'Invalid token'}),400
    
    if token_verification_status == 'Token is valid':
        if 'image' not in data:
            return jsonify({'error': 'No image path provided'}), 400
        if 'encryption_key' not in data:
            return jsonify({'error': 'No encryption key provided'}), 400
        
        encryption_key_hex = data['encryption_key']
        image_data_byte = data['image']
    
        # Convert hex string back to bytes
        try:
            encryption_key = base64.b64decode(encryption_key_hex)
    
        except ValueError:
            return jsonify({'error': 'Invalid encryption key format'}), 400
        try:
            image_data = base64.b64decode(image_data_byte) 
        except Exception as e:
            print(e)
            return jsonify({'error': e}), 400
        try:
            path = decrypt_v4(image_data,encryption_key)
            # buffered = BytesIO()
            # path.save(buffered, format="PNG")
            return jsonify({'image': base64.b64encode(path).decode('utf-8')}), 200
            # print(decrypted_data)
            return send_file(decrypted_data,mimetype='image/jpeg', as_attachment=True, download_name='decrypted_image.jpg')
        except Exception as e:
            print(e)
            return jsonify({'error': "error while processing file"}), 500
    return jsonify({'error':'Something Went Wrong while fullfilling your request'}),500


@app.route('/decrypt_v2', methods=['POST'])
def decrypt_image_with_name():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid API key'}), 401

    api_key = auth_header.split()[1]  # Extract API key from header
    if api_key !=  config_dict['API_KEY']:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    if 'image_path' not in data:
        return jsonify({'error': 'No image path provided'}), 400
    if 'encryption_key' not in data:
        return jsonify({'error': 'No encryption key provided'}), 400
    
    encryption_key_hex = data['encryption_key']

    # Convert hex string back to bytes
    try:
        encryption_key = base64.b64decode(encryption_key_hex)
        print(encryption_key)
    except ValueError:
        return jsonify({'error': 'Invalid encryption key format'}), 400
    image_path = data['image_path']
    base_image_path = os.path.join(config_dict['base_dir'],config_dict["processed_dir"],config_dict["enc_image_dir"])
    # Construct the full path to the image file
    if "_AP1." in image_path:
        full_image_path = os.path.join(base_image_path,"AP1",image_path)
    # Check if the file exists
    if not os.path.isfile(full_image_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        # Send the file to the client
        if full_image_path.split('.')[-1] == 'enc':

            path = decrypt_v4(full_image_path,encryption_key)

            decrypted_data = BytesIO(path)
        return send_file(decrypted_data,mimetype='image/jpeg', as_attachment=True, download_name='decrypted_image.jpg')
    except Exception as e:
        return jsonify({'error': "wrong encryption key"}), 500
    #old approch
    # print(data)
    # if 'images' not in request.files:
    #     return jsonify({'error': 'No images found'}), 400

    # images_folder = request.files.getlist('images')
    # images_paths = []
    # print(images_paths)
    # for idx, image_file in enumerate(images_folder):
    #     IMAGE_PATH = os.path.join("encrypted", image_file.filename)
    #     print(IMAGE_PATH)
    #     images_paths.append(IMAGE_PATH)
    # print(images_paths)
    # masked_images_paths = []

    # for image_path in images_paths:
    #     if image_path.split('.')[-1] == 'enc':
    #         path = decrypt_v4(image_path)
    # return jsonify({'decrypted_images_paths': path}), 200


@app.route('/mask_maker_v3', methods=['POST'])
def apply_mask_to_folder_filename_only():
    # auth_header = request.headers.get('Authorization')
    # if not auth_header or not auth_header.startswith('Bearer '):
    #     return jsonify({'error': 'Missing or invalid API key'}), 401

    # api_key = auth_header.split()[1]  # Extract API key from header
    # if api_key != API_KEY:
    #     return jsonify({'error': 'Unauthorized'}), 403

    if 'images' not in request.files:
        return jsonify({'error': 'No images found'}), 400

    images_folder = request.files.getlist('images')

    images_paths = []

    f = open( images_folder[0].filename, "r")
    for idx, image_file in enumerate(f.readlines()):
        image_file = image_file.rstrip()
        IMAGE_PATH = os.path.join("images", image_file)
        images_paths.append(IMAGE_PATH)

    masked_images_paths = []
    

    for image_path in images_paths:
        masked_image = mask_maker_v2(image_path)

        masked_images_paths.append({image_path:masked_image})

    # Specify the CSV file path
    csv_file = 'data.csv'

    # Open CSV file for writing
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write header (optional for single dictionary)
        writer.writerow(['Key', 'Value'])

        # Write data rows
        for i in masked_images_paths:
            writer.writerow(i.items())

    print(f'CSV file "{csv_file}" has been created successfully.')
    # for image_path in images_paths:
    #     os.remove(image_path)

    return jsonify({'masked_images_paths': masked_images_paths}), 200




# Endpoint to generate a token
@app.route('/generate-token', methods=['GET'])
def generate_token_endpoint():
    
    token = generate_token()
    
    return jsonify({
        "message": "Token generated successfully",
        "token": token
    })




if __name__ == '__main__':
    app.run(host='0.0.0.0')
