#!/bin/bash

#activate virtual env
source /reports/Image_masking_test_api/virtual_env/pocr_env/bin/activate
#. ./.bash_profile
. /reports/.bash_profile
export LD_LIBRARY_PATH=/oracle/app/oracle/product/19.0.0/client_1/instantclient:$LD_LIBRARY_PATH
export PATH=/oracle/app/oracle/product/19.0.0/client_1/instantclient:$PATH

#run python script

cnt=$(ps -ef|grep run_legacy_re_processor|grep -v grep|wc -l)
echo $cnt "|" `date` >>/reports/Image_masking_test_api/image_mask/logs/re_process_logfil.log
if [ $cnt -gt 3 ]; then
    exit 0
else
	echo "Moved into else part to execute python script"
    if ! /reports/Image_masking_test_api/virtual_env/pocr_env/bin/python3.12 /reports/Image_masking_test_api/image_mask/legacy_re_processor.py; then
    #if command fails send email
        echo 'An error occured while running the legacy_re_processor script.' |mail -s "Image Masking script error" prince.a@sgcsol.com,priyanka.s@sgcsol.com
    else
        echo 'Execution of the cronjob legacy_re_processor is compleated. please check logs for more details.' |mail -s "Image Masking script completion" prince.a@sgcsol.com,priyanka.s@sgcsol.com
    fi
fi

