import os
from datetime import datetime
import cx_Oracle
import json
import sys
import time
#credentials
try:
    username = 'KYCDOC'
    password = 'Welcome#8765'
    dsn = '172.20.20.24:1212/misdb'
    connection = cx_Oracle.connect(user=username,password=password,dsn=dsn)
    cursor = connection.cursor()
    print(cursor)
except Exception as e:
    print("not able to create connection due to ",e)
    sys.exit(1)

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

draft_list = []
def get_recent_files(directory,time_threshold,current_time,output_file_name):
    try:
        with open(output_file_name, 'r') as file:
            files = file.readlines()
            files = [line.strip() for line in files]
    except Exception as e:
        print(e)
        files = []
    print(len(files))
    start_len = len(files)
    #draft_list = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory,filename)
        if os.path.isfile(filepath):
            creation_time = os.path.getctime(filepath)
            #if current_time - creation_time <= time_threshold:
            if creation_time >= 1747668290180:
                files.append(filepath)
                draft_list.append(filename.split('_')[0])
    files = list(set(files))
    with open(output_file_name, 'w') as file:
        if len(files) > 0:
            for filepath in files:
                file.write(f"{filepath}\n")
            print(f"new {len(files)- start_len } files written on {output_file_name}")
        else:
            print(f"no new files available for {output_file_name}")
    return draft_list

def get_recent_files_new(directory,time_threshold,current_time,output_file_name,last_watermark_entry):
    try:
        with open(output_file_name, 'r') as file:
            files = file.readlines()
            files = [line.strip() for line in files]
    except Exception as e:
        print(e)
        files = []
    print(len(files))
    #draft_list = []
    max_c_time = last_watermark_entry
    for filename in os.listdir(directory):
        filepath = os.path.join(directory,filename)
        if os.path.isfile(filepath):
            creation_time = os.path.getctime(filepath)
            max_c_time = max(max_c_time,creation_time)
            if (creation_time >= last_watermark_entry): #or (current_time - creation_time <= time_threshold) :
                files.append(filepath)
                draft_list.append(filename.split('_')[0])
    files = list(set(files))
    with open(output_file_name, 'w') as file:
        if len(files) > 0:
            for filepath in files:
                file.write(f"{filepath}\n")
            print(f"new {len(files)} files written on {output_file_name}")
        else:
            print(f"no new files available for {output_file_name}")
    return max_c_time



if __name__ == "__main__":
    directory_to_check = ['AP1','AP2','PI1','PI2']
    base_image_dir = '/reports/Image_masking_test_api/image_mask/images/ip_dir/Originals/'
    current_time = datetime.now().timestamp()
    start_time = current_time
    log_wm_file_path = '/reports/Image_masking_test_api/image_mask/watermark_data.json'
    last_wm_file = '/reports/Image_masking_test_api/image_mask/last_wm.txt'
    initial_c_time = int(time.time())
    max_c_time = int(time.time())
    with open(last_wm_file,'r') as f:
        last_watermark_entry = float(f.read().splitlines()[-1].strip())
        print("last watermark entry: ",last_watermark_entry)
    wm_file_path = '/reports/Image_masking_test_api/image_mask/watermark_data.json'
    for directory in directory_to_check:
        output_file_path = f"/reports/Image_masking_test_api/image_mask/output_file_new.txt"
        max_c_time = get_recent_files_new(os.path.join(base_image_dir,directory),5*60,current_time,output_file_path,last_watermark_entry)
        print('processing time : ',time.time()-start_time)
        start_time = time.time()
    with open(wm_file_path,'r') as wm_file:
        data = json.load(wm_file)
    initial_length = len(data)
    print("total new drafts ",len(draft_list))
    for draft_id in draft_list:
        try:
            cursor.execute(fetch_sql,draftid = draft_id)
            rows = cursor.fetchall()
            if len(rows)>0:
                for row in rows:
                    watermark_text =  [f"Lat {row[0]} | Long {row[1]} | accountNo {row[2]}" ,f"POS Name {row[3]} {row[4]} | POS Code {row[5]} ", f"Date and Time {row[6]} "]

            #if data.get(draft_id,'record not available') == 'record not available':
                data[draft_id] = watermark_text
        except Exception as e:
            print(f"exception {e} happen during fetching watermark records for {draft_id}")
    print("new dict length", len(data)- initial_length)
    with open(wm_file_path,'w') as wm_file:
        json.dump(data,wm_file,indent = 4)
   # if max_c_time == last_watermark_entry:
    #    max_c_time = initial_c_time
    print("last watermark time : ",max_c_time)
    with open(last_wm_file,'w') as last_wm_file :
        last_wm_file.write(str(max_c_time))
    print("adding watermark info done")

#old change start
'''
    wm_file_path = '/reports/Image_masking_test_api/image_mask/watermark_data.json' 
    for directory in directory_to_check:
        output_file_path = f"/reports/Image_masking_test_api/image_mask/output_file_{directory}.txt"
        get_recent_files(os.path.join(base_image_dir,directory),24*60*60,current_time,output_file_path)
     
    with open(wm_file_path,'r') as wm_file:
        data = json.load(wm_file)
    for draft_id in draft_list:
        try:
            cursor.execute(fetch_sql,draftid = draft_id)
            rows = cursor.fetchall()
            if len(rows)>0:
                for row in rows:
                    watermark_text =  [f"Lat {row[0]} | Long {row[1]} | accountNo {row[2]}" ,f"POS Name {row[3]} {row[4]} | POS Code {row[5]} ", f"Date and Time {row[6]} "]

            if data.get(draft_id,'record not available') == 'record not available':
                data[draft_id] = watermark_text
        except Exception as e:
            print(f"exception {e} happen during fetching watermark records for {draft_id}")
    with open(wm_file_path,'w') as wm_file:
        json.dump(data,wm_file,indent = 4)
    print("adding watermark info done")
#old change end

#new change start

    log_wm_file_path = '/reports/Image_masking_test_api/pre_prod_image_mask/watermark_data.json'
    with open(log_wm_file_path,'r') as f:
        last_watermark_entry = float(f.read().splitlines()[-6].strip()[1:-4])
    
    wm_file_path = '/reports/Image_masking_test_api/pre_prod_image_mask/temp_watermark_data.json'
    for directory in directory_to_check:
        output_file_path = f"/reports/Image_masking_test_api/pre_prod_image_mask/output_file.txt"
        get_recent_files_new(os.path.join(base_image_dir,directory),5*60,current_time,output_file_path,last_watermark_entry)
        print('processing time : ',time.time()-start_time)
        start_time = time.time()
    with open(wm_file_path,'r') as wm_file:
        data = json.load(wm_file)
    for draft_id in draft_list:
        try:
            cursor.execute(fetch_sql,draftid = draft_id)
            rows = cursor.fetchall()
            if len(rows)>0:
                for row in rows:
                    watermark_text =  [f"Lat {row[0]} | Long {row[1]} | accountNo {row[2]}" ,f"POS Name {row[3]} {row[4]} | POS Code {row[5]} ", f"Date and Time {row[6]} "]

            #if data.get(draft_id,'record not available') == 'record not available':
                #data[draft_id] = watermark_text
        except Exception as e:
            print(f"exception {e} happen during fetching watermark records for {draft_id}")
    with open(wm_file_path,'w') as wm_file:
        json.dump(data,wm_file,indent = 4)
    if len(data.keys())>0:
        with open(log_wm_file_path,'a') as log_wm_file :
            json.dump(data,log_wm_file,indent = 4)
    print("adding watermark info done")

'''
#new change end
