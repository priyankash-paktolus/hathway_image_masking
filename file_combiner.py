f1_path = '/reports/Image_masking_test_api/image_mask/filtered_output_file.txt'
f2_path = '/reports/Image_masking_test_api/image_mask/output_file_new.txt'

top_n_lines = []
remaining_files = []
with open(f1_path, 'r') as file1:
    for i,line in enumerate(file1):
        if i < 10:
            top_n_lines.append(line)
        else:
            remaining_files.append(line)

with open(f2_path,'a') as file2:
    file2.write('\n')
    file2.writelines(top_n_lines)

with open(f1_path,'w') as file1:
    file1.writelines(remaining_files)

print(f"writing old files done {len(remaining_files)} files remains")
