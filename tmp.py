import os

def main():
    
    # Example usage:
    directory_path = "C:\\Users\\rapha\\Pictures\\Albion\\Albion Items\\Weapons"
    all_files = get_all_files(directory_path)
    print(len(all_files))
    with open("weaponNames.txt",'w') as f:
        for file in all_files:
            print(file[:len(file)-4])
            f.write(file[:len(file)-4].strip().lower() + '\n')

import os

def get_all_files(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower() != "desktop.ini":
                file_list.append(file)
    return file_list



if __name__ == "__main__":
    main()