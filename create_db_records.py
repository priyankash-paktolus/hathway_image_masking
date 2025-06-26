import os
from datetime import datetime
import cx_Oracle
import json
import sys
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


file_path = 'output_no_duplicates.txt'
with open(file_path,'r',encoding='utf-8') as file:
    lines = file.readlines()
    draft_list = [line.strip() for line in lines]

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
try:
    with open('new_watermark_data.json','w') as wm_file:
        json.dump(data,wm_file,indent = 4)
except:
    print("not able to write data in file")
print("adding watermark info done")
