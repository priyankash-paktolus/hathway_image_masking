#!/bin/bash

#get count from each directory

ENC_COUNT=$(find /reports/Image_masking_test_api/image_mask/images/op_dir/masked -type f -mtime -1 | wc -l)

#MSK_COUNT=$(find /reports/Image_masking_test_api/image_mask/images/processed_images/masked -type f -mtime -1 | wc -l)

CURRENT_DATE=$(date +"%Y-%m-%d %H:%M:%S")
#Email setting

#EMAIL="prince.a@sgcsol.com,priyanka.s@sgcsol.com"
EMAIL="priyanka.s@sgcsol.com"

SUBJECT="File Count in last 24 hours"

BODY="As per $CURRENT_DATE , There are $ENC_COUNT newly watermarked images in last 24hours"


#send Enail

#echo "$BODY" |mail -s "$SUBJECT" "$EMAIL"
echo "Last 24 Hours count on $CURRENT_DATE for Encry $ENC_COUNT and Masked $MSK_COUNT" |mail -s "File Count in last 24 hour" priyanka.s@sgcsol.com,prince.a@sgcsol.com

