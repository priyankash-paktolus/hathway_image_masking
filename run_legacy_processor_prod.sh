#!/bin/bash

#activate virtual env
source /reports/Image_masking_test_api/virtual_env/pocr_env/bin/activate
. ./.bash_profile
export LD_LIBRARY_PATH=/oracle/app/oracle/product/19.0.0/client_1/instantclient:$LD_LIBRARY_PATH
export PATH=/oracle/app/oracle/product/19.0.0/client_1/instantclient:$PATH

#run python script

cnt=$(ps -ef|grep run_legacy_processor|grep -v grep|wc -l)
echo $cnt "|" `date` >>/reports/Image_masking_test_api/image_mask/logs/logfile_pre_prod_new.log
if [ $cnt -gt 3 ]; then
    exit 0
else
    /reports/Image_masking_test_api/virtual_env/pocr_env/bin/python3.12 /reports/Image_masking_test_api/image_mask/file_combiner.py
    /reports/Image_masking_test_api/virtual_env/pocr_env/bin/python3.12 /reports/Image_masking_test_api/image_mask/new_file_checker.py
    if ! /reports/Image_masking_test_api/virtual_env/pocr_env/bin/python3.12 /reports/Image_masking_test_api/image_mask/legacy_processor.py; then
    #if command fails send email
        echo 'An error occured while running the legacy_processor script.' |mail -r "srtadmin@hathway.net" -s "Image Masking script error" prince.a@sgcsol.com,priyanka.s@sgcsol.com
    else
        echo "CRON JOB Execution Completed" |mail -r "srtadmin@hathway.net" -s "Image Masking Job completion" prince.a@sgcsol.com,priyanka.s@sgcsol.com
    fi
fi




