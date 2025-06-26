import os
from datetime import datetime, timedelta
from mask_ids_v2 import mask_maker_v2
import time,json
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
# Define the SQL INSERT statement
insert_sql = """
INSERT INTO poi_poa_masking_logs (timestamp, file_size, document_type, status, path)
VALUES (:1, :2, :3, :4, :5)
"""

fetch_sql = """
SELECT
    sales.lattitude,
    sales.longitude,
    sales.obrm_accno,
    COLLECTION_PORTAL.USERMASTER.FIRSTNAME,
    COLLECTION_PORTAL.USERMASTER.LASTNAME,
    sales.agent_id,
    sales.created_ts
FROM
    FOS.SALES_CUSTOMER_DETAIL sales
JOIN
    COLLECTION_PORTAL.USERMASTER
    ON COLLECTION_PORTAL.USERMASTER.EU_SALES_NAME = sales.agent_id
WHERE
    sales.draftid = :draftid
"""

def process_recently_created_files_ap1(file_path):
    print(f"process started for {file_path} at {datetime.now()}",flush = True)
    key = "7utxcIOCk+uLPbgRl6d2/xIqbXJ65HX9I+HfptVVcHM="
    """Store names of files created in the last 'minutes' minutes into a text file."""
    buffer_time = 60
    temp_file_path = file_path + '.tmp'
    pro_file_path = file_path + '.pro'
   # count = int(time.time()) + buffer_time
    try:
        with open('/reports/Image_masking_test_api/image_mask/watermark_data.json','r') as wm_file:
       # with open('/reports/Image_masking_test_api/image_mask/temp_watermark_data.json','r') as wm_file: #new changes

            watermark_data = json.load(wm_file)
    except Exception as e:
        print("watermark info not available ",e)
        watermark_data = {}

    count = 0
    file_available = []
    with open(file_path, 'r') as infile, open(temp_file_path, 'w') as outfile, open(pro_file_path, 'w') as profile:
        for line in infile:
            image_name = line.strip()
            if not os.path.isfile(image_name):
                print(f"Image file does not exist: {image_name}",flush = True)
                continue
 
            if count >= 500 : # int(time.time()):
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
                try:
                    image = cv2.imread(img_path)
                except:
                    print('error reading files')
                    # return 500,document_type,"Some issue with loading the image , please check image path", document_path
                draft_id = img_name.split("_")[0]
                watermark_text = watermark_data.get(draft_id,"record not available")		
                if watermark_text == "record not available":
                    #new changes below
                    print(f"record not available for {draft_id} , fetching raw from DB",flush = True)
                    #continue
                    cursor.execute(fetch_sql,draftid = draft_id)
                    rows = cursor.fetchall()
                    if len(rows)>0:
                        for row in rows:
                            watermark_text =  [f"Lat {row[0]} | Long {row[1]} | accountNo {row[2]}" ,f"POS Name {row[3]} {row[4]} | POS Code {row[5]} ", f"Date and Time {row[6]} "]

                    else:
                        outfile.write(line)
                        print(f"record not available for {draft_id} in DB",flush = True)
                        continue
                
                try:
                    try:
                        status_code,document_type,status,processed_image = mask_maker_v2(image,key)
                    except Exception as e:
                        print("error while masking ",e)
                    masked_image_name = f"{img_name}_m.{ext}"
                    masked_image_path = f"{os.path.join(config_dict["base_dir"],config_dict["op_dir"],config_dict["masked_image_dir"],os.path.basename(os.path.dirname(img_path)),f"{img_name}.{ext}")}"
#                    print(masked_image_path)
                    try:
                        watermarked_masked_image = add_watermark2(processed_image,watermark_text)
                    except Exception as e:
                        print("error while watermarking  ",e)
                    try:
                        watermarked_masked_image.save(masked_image_path)
                    except Exception as e:
                        print("error while watermarking saving ",e)
                    # cv2.imwrite(masked_image_path, watermarked_masked_image)
                    # image_name = IMAGE_PATH[7:]
                    try:
                        enc_masked_image = add_watermark2(image,watermark_text)
                    except Exception as e:
                        print("error while wat ermarking env=c  ",e)
                    try:
                        org_buffered = BytesIO()
                        ext_format = "JPEG"
                        if ext.upper() == "PNG":
                            ext_format = "PNG"
                        enc_masked_image.save(org_buffered, format=ext_format )
                        encrypted_image_path = encrypt_v4(org_buffered.getvalue(),img_path, img_name,ext,key)
                    except Exception as e:
                        print("error while enc  ",e)
                    try:
                        source_path = img_path
                        #destination_path = img_path.replace('Originals','destined')
                       # print(destination_path)
                        # Move the file
                       # shutil.move(source_path, destination_path)
                        current_time = datetime.now()
                        file_size = os.path.getsize(source_path)
            
                        data = (
                        current_time,            # Timestamp
                        file_size,              # File size
                        document_type,          # Document type
                        status,                 # Status
                        masked_image_path    # Path
                        )
                        profile.write(line)
                        
#                        try:
                            # Execute the insert statement
 #                           cursor.execute(insert_sql, data)
                                            # Commit the transaction
  #                          connection.commit()
                           # print("Data inserted successfully.")
   #                     except cx_Oracle.DatabaseError as e:
                            #    outfile.write(line)
    #                        print(f"An error occurred: {e} while processing {source_path}",flush = True)
                        
                        count += 1
#                        print(f"succesfully processed : {line} ",flush = True)
                    except Exception as e:
                        outfile.write(line)
                        print(f"An error occurred: {e} while processing {source_path}",flush = True)
                except Exception as e:
                    print(e)
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
#    txt_file_path = '/reports/Image_masking_test_api/pre_prod_image_mask/output_file.txt' #new change
    # process_recently_created_files_ap1(txt_file_path)
    try:
#        t1 = multiprocessing.Process(target=process_recently_created_files_ap1, args=(f"{txt_file_path}AP1.txt",))
#        t2 = multiprocessing.Process(target=process_recently_created_files_ap1, args=(f"{txt_file_path}AP2.txt",))
        t3 = multiprocessing.Process(target=process_recently_created_files_ap1, args=(f"{txt_file_path}new.txt",))
        #t4 = multiprocessing.Process(target=process_recently_created_files_ap1, args=(f"{txt_file_path}PI2.txt",))
        #print("start time: ", datetime.now()) #new changes
        #process_recently_created_files_ap1(txt_file_path) #new changes

    except Exception as e:
        print(e)
    print("start time: ",datetime.now())
    try:
 #       t1.start()
  #      t2.start()
        t3.start()
        #t4.start()
    except Exception as e:
        print(e)

    try:
   #     t1.join()
    #    t2.join()
        t3.join()
       # t4.join()
    except Exception as e:
        print(e)

#reprocessing
    try:
        tmp_files_list = ["AP1.txt.tmp","AP2.txt.tmp","new.txt.tmp"]
        for file in tmp_files_list:
            file_path = f"{txt_file_path}{file}"
            if os.path.exists(file_path):
          
                tmp_file = file_path
                pro_file = file_path.replace(".tmp",".pro")
                main_file = file_path.replace(".tmp","")
               
                with open(tmp_file,'r') as tmp:
                    tmp_lines = tmp.readlines()


                with open(pro_file,'r') as pro:
                    pro_lines = pro.readlines()

                with open(main_file,'r') as mainf:
                    main_lines = mainf.readlines()

                if len(tmp_lines) > 0:
                    with open(main_file, 'a') as mainf:
                        mainf.writelines(tmp_lines)
                if len(pro_lines) > 0:
                    with open(main_file,'r') as mainf:
                        updated_lines = [line for line in mainf if line.strip() not in pro_lines]

                    with open(main_file,'w') as mainf:
                        mainf.writelines(updated_lines)
                os.remove(tmp_file)
                print(f"{len(pro_lines)}files processed from {main_file} at {datetime.now()}",flush = True)
    except Exception as e:
        print(e)
    print("end time: ",datetime.now())
    print("processing time: ",(time.time()-start_time)/60)
    try:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()
