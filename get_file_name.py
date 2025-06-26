
import os
from config import config_dict
base_dir = '/reports/Image_masking_test_api/image_mask/images/ip_dir/Originals'
sec_dir = "/reports/Image_masking_test_api/image_mask/images/op_dir/masked"

available_list = [1726212100558,1729753965363,1729857175079,1729860159932,1730274554576,1730294984361,1730300398764,1730725868733,1730805564993]
if __name__ == "__main__":

    for directory in config_dict["directories_to_check"]:
        output_file_path = f"output_file_{directory}.txt"
        ip_directory = os.path.join(base_dir,directory)
        org_dir = os.path.join(sec_dir,directory)
        file_names_main = os.listdir(ip_directory)
        file_names_main = [f.replace('.enc','') for f in file_names_main if os.path.isfile(os.path.join(ip_directory, f))]  
        file_names_sec = os.listdir(org_dir)
        file_names_sec = [f.replace('.enc','') for f in file_names_sec if os.path.isfile(os.path.join(org_dir, f))]
        file_names = set(file_names_main) - set(file_names_sec)
        print(f"{output_file_path} : {len(file_names)}")
        with open(output_file_path, 'w') as f:
            for filename in file_names:
                f.write(f"{os.path.join(ip_directory ,filename)}" + '\n')

    print(f'File names have been written to {output_file_path}')
