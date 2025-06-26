import os,json
from datetime import datetime, timedelta
from mask_ids_v2 import mask_maker_v2
import time
import shutil
from config import config_dict
import time
import multiprocessing
from datetime import datetime
import time
import cx_Oracle
import sys
from utils_v2 import get_draft_id,add_watermark2,encrypt_v4
import cv2
from io import BytesIO
#credentials
'''
try:
    username = 'KYCDOC'
    password = "Welcome#8765"


    # Define your Oracle DSN and credentials
    dsn = '172.20.20.24:1212/misdb'  # Replace with your DSN

    # Establish the connection
    connection = cx_Oracle.connect(user=username, password=password, dsn=dsn)

# Create a cursor
    cursor = connection.cursor()
    print(cursor,flush = True)
except Exception as e:
    print("not able to create database connection due to ",e)
    sys.exit(1) 

'''
# Define the SQL INSERT statement
insert_sql = """
INSERT INTO poi_poa_masking_logs (timestamp, file_size, document_type, status, path)
VALUES (:1, :2, :3, :4, :5)
"""
fetch_sql ="""
SELECT 
    sales.lattitude,
    sales.longitude,
    sales.obrm_accno,
    COLLECTION_PORTAL.USERMASTER.FIRSTNAME,
    COLLECTION_PORTAL.USERMASTER.LASTNAME,
    sales.agent_id,
    sales.created_ts
FROM 
    FOSPREPROD.SALES_CUSTOMER_DETAIL sales
JOIN 
    COLLECTION_PORTAL.USERMASTER 
    ON COLLECTION_PORTAL.USERMASTER.EU_SALES_NAME = sales.agent_id
WHERE 
    sales.draftid = :draftid
"""

try:
    with open('/reports/Image_masking_test_api/image_mask/watermark_data.json','r') as wm_file:
        watermark_data = json.load(wm_file)
except Exception as e:
    print("watermark info not available ",e)
    sys.exit(1)



def process_recently_created_files_ap1(file_path):
    print(f"process started for {file_path} at {datetime.now()}",flush = True)
    key = "7utxcIOCk+uLPbgRl6d2/xIqbXJ65HX9I+HfptVVcHM="
    """Store names of files created in the last 'minutes' minutes into a text file."""
    buffer_time = 60
    temp_file_path = file_path + '.tmp'
    pro_file_path = file_path + '.pro'
   # count = int(time.time()) + buffer_time
    count = 0
   # try:
     #   with open('/reports/Image_masking_test_api/image_mask/watermark_data.json','r') as wm_file:
    #        watermark_data = json.load(wm_file)
   # except Exception as e:
      #  print("watermark info not available ",e)
     #   return -1
    file_available = []
    with open(file_path, 'r') as infile, open(temp_file_path, 'w') as outfile, open(pro_file_path, 'w') as profile:
        for line in infile:
            image_name = line.strip()
            if not os.path.isfile(image_name):
                print(f"Image file does not exist: {image_name}",flush = True)
                continue

            if count >= 5000 : # int(time.time()):
                outfile.write(line)
                continue
            if image_name:
                img_path = image_name
                masked_image = ""
                try:
                    _,img_full = os.path.split(img_path)
                except Exception as e:
                    img_full = img_path
                img_name,ext = img_full.rsplit('.',1)
                
                draft_id = img_name.split("_")[0]
                watermark_text = watermark_data.get(draft_id,"record not available")		
                if watermark_text == "record not available":
                    outfile.write(line)
                    print(f"record not available for {draft_id}",flush = True)
                    continue
                try:
                    
                    try:
                        #  status_code,document_type,status,processed_image = mask_maker_v2(image,key)
                        processed_image_path = img_path.replace('Originals',os.path.join('processed_images','masked'))
                        directory, filename = os.path.split(processed_image_path)
                        masked_image_name = f"{img_name}_m.{ext}"
                        masked_image_path = f"{os.path.join(config_dict["base_dir"],config_dict["op_dir"],config_dict["masked_image_dir"],os.path.basename(os.path.dirname(img_path)),f"{img_name}.{ext}")}"

                        processed_image_path  = os.path.join(directory,masked_image_name) 
                        if not os.path.isfile(processed_image_path): 
                            #print(f"masked Image file does not exist: {image_name}",flush = True)
                            if os.path.isfile(img_path):
                                #print("got original unsupported")
                                processed_image = cv2.imread(img_path)
                            else:
                                #print("Image file not available")
                                outfile.write(line)
                                continue
                        else:
                            #print("got masked",processed_image_path)
                            processed_image = cv2.imread(processed_image_path)
                    except Exception as e:
                        print(e)
                        outfile.write(line)
                        continue
                    try:
                        watermarked_masked_image = add_watermark2(processed_image,watermark_text)
                        #print("watermarking of original done")
                    except Exception as e:
                        print(f"error while watermarking {e} ",flush = True)
                        outfile.write(line)
                        continue
                    try:
                        watermarked_masked_image.save(masked_image_path)
                        #print("saving original done",masked_image_path)
                    except Exception as e:
                        print(f"error while watermarking saving {e}",flush = True)
                        outfile.write(line)
                        continue
                    # cv2.imwrite(masked_image_path, watermarked_masked_image)
                    # image_name = IMAGE_PATH[7:]
                    try:
                        image = cv2.imread(img_path)
                        enc_masked_image = add_watermark2(image,watermark_text)
                        #print("watermarking of enc done")
                    except Exception as e:
                        print(f"error while watermarking encrypted file :{e}",flush = True)
                        outfile.write(line)
                        continue
                    try:
                        org_buffered = BytesIO()
                        ext_format = "JPEG"
                        if ext.upper() == "PNG":
                            ext_format = "PNG"
                        enc_masked_image.save(org_buffered, format=ext_format )
                        encrypted_image_path = encrypt_v4(org_buffered.getvalue(),img_path, img_name,ext,key)
                        #print("saving of enc done")
                    except Exception as e:
                        print(f"error while enc {e} ",flush = True)
                        outfile.write(line)
                        continue

                    count += 1
                except Exception as e:
                    print(e,flush = True)
                    outfile.write(line)

#    print(file_available)
    try:    
        os.remove(file_path)
        os.rename(temp_file_path, file_path)
    except:
        print(f"not able to update {file_path}",flush = True)
    print(f"{count}files processed from {file_path} at {datetime.now()}",flush = True)        
def main():
    start_time = time.time()
    txt_file_path = '/reports/Image_masking_test_api/image_mask/output_file_'  # Path to your text file with image names
    # process_recently_created_files_ap1(txt_file_path)
    try:
        t1 = multiprocessing.Process(target=process_recently_created_files_ap1, args=(f"{txt_file_path}AP1.txt",))
        t2 = multiprocessing.Process(target=process_recently_created_files_ap1, args=(f"{txt_file_path}AP2.txt",))
        t3 = multiprocessing.Process(target=process_recently_created_files_ap1, args=(f"{txt_file_path}PI1.txt",))
        t4 = multiprocessing.Process(target=process_recently_created_files_ap1, args=(f"{txt_file_path}PI2.txt",))
    except Exception as e:
        print(e)
    print("start time: ",datetime.now())
    try:
        t1.start()
        t2.start()
        t3.start()
        t4.start()
    except Exception as e:
        print(e)

    try:
        t1.join()
        t2.join()
        t3.join()
        t4.join()
    except Exception as e:
        print(e)

    print("end time: ",datetime.now())
    print("processing time: ",(time.time()-start_time)/60)


if __name__ == '__main__':
    main()
