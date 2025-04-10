
import os
import json
import mmap
from binascii import hexlify, unhexlify, b2a_hex

import pandas as pd

def str_to_list(hex_line):
    Time = hex_line[0:8]
    Voltage = hex_line[8:12]
    Current = hex_line[12:16]
    Capacity = hex_line[16:24]
    Power = hex_line[24:36]
    return [Time, Voltage, Current, Capacity, Power]

def string_to_hex(byte):
    hex_string = byte
    hex_values = [hex(int(hex_string[i:i+2], 16))[2:].zfill(2) for i in range(0, len(hex_string), 2)]
    return "\\x" + "\\x".join(hex_values)

def create_dict(file):
    df = pd.read_excel(file)
    my_dict = {}
    for index, row in df.iterrows():
        key = row["Voltage"]
        value = row["Voltage_Value"]
        if pd.isnull(value):
            my_dict[key] = {}
        else:
            my_dict[key] = value
    with open("my_dict.json", "w") as f:
        json.dump(my_dict, f)

def creat_csv_dict(file):
    df = pd.read_csv(file, encoding='gbk')
    start_reading = False
    filtered_data = pd.DataFrame()
    for index, row in df.iterrows():
        if row[0] == "记录序号":
            start_reading = True
            continue
        if row[0] == "工步序号":
            start_reading = False
            continue
        if start_reading:
            filtered_data = filtered_data.append(row)
    return filtered_data

def update_dict(file):
    with open("my_dict.json", "r") as f:
        my_dict = json.load(f)
    new_df = pd.read_excel(file)
    for index, row in new_df.iterrows():
        key = row["Voltage"]
        value = row["Voltage_Value"]
        my_dict[key] = value
    with open("my_dict.json", "w") as f:
        json.dump(my_dict, f)

def read_cex(file):
    with open(file, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        mm_size = mm.size()
        identifier = b'\xbb\xbb\xff\xff\x13\x00'
        header = mm.find(identifier) + 16
        output = []
        output_stop = []
        previous_condition = "if"
        for add in range(header, mm_size, 16):
            mm.seek(add)
            byte = mm.read(16)
            hex_line = hexlify(byte).decode('utf-8')
            if hex_line.startswith("ccccffff") or hex_line.startswith("cdccffff"):
                if previous_condition == "else":
                    output_stop.append([])
                output_stop.append(str_to_list(hex_line))
                previous_condition = "if"
            else:
                output.append(str_to_list(hex_line))
                previous_condition = "else"
        df = pd.DataFrame(output, columns=["Time", "Voltage", "Current", "Capacity", "Power"])
        df_stop = pd.DataFrame(output_stop, columns=["Time", "Voltage", "Current", "Capacity", "Power"])
        df.index += 1
        df_stop.index += 1
        df.to_csv("output_code.csv", index=True)
        df_stop.to_csv("output_stop_code.csv", index=True)
        return df

def hebing(df1, df2):
    df = pd.concat([df1, df2], axis=1)
    with open("my_dict_voltage.json", "r") as f:
        my_dict_voltage = json.load(f)
    with open("my_dict_curr.json", "r") as f:
        my_dict_curr = json.load(f)
    with open("my_dict_capacity.json", "r") as f:
        my_dict_capacity = json.load(f)
    with open("my_dict_power.json", "r") as f:
        my_dict_power = json.load(f)
    with open("my_dict_test_time.json", "r") as f:
        my_dict_test_time = json.load(f)
    for index, row in df.iterrows():
        my_dict_voltage[row["Voltage"]] = row["放电能量(mWh)"]
        my_dict_curr[row["Current"]] = row["充电比容量(mAh/g)"]
        my_dict_capacity[row["Capacity"]] = row["放电比容量(mAh/g)"]
        my_dict_power[row["Power"]] = row["充电中压(V)"]
        my_dict_test_time[row["Time"]] = row["充电容量(mAh)"]
    with open("my_dict_voltage.json", "w") as f:
        json.dump(my_dict_voltage, f)
    with open("my_dict_curr.json", "w") as f:
        json.dump(my_dict_curr, f)
    with open("my_dict_capacity.json", "w") as f:
        json.dump(my_dict_capacity, f)
    with open("my_dict_power.json", "w") as f:
        json.dump(my_dict_power, f)
    with open("my_dict_test_time.json", "w") as f:
        json.dump(my_dict_test_time, f)

def cex_to_txt(file):
    with open(file, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        mm_size = mm.size()
        identifier = b'\xbb\xbb\xff\xff\x13\x00'
        header = mm.find(identifier) + 16
        output = []
        output_stop = []
        previous_condition = "if"
        for add in range(header, mm_size, 16):
            mm.seek(add)
            byte = mm.read(16)
            hex_line = hexlify(byte).decode('utf-8')
            if hex_line.startswith("ccccffff") or hex_line.startswith("cdccffff"):
                if previous_condition == "else":
                    output_stop.append([])
                output_stop.append(str_to_list(hex_line))
                previous_condition = "if"
            else:
                output.append(str_to_list(hex_line))
                previous_condition = "else"
        df = pd.DataFrame(output, columns=["Time", "Voltage", "Current", "Capacity", "Power"])
        df_stop = pd.DataFrame(output_stop, columns=["Time", "Voltage", "Current", "Capacity", "Power"])
    with open("my_dict_voltage.json", "r") as f:
        my_dict_voltage = json.load(f)
    for index, row in df.iterrows():
        key_value = row["Voltage"]
        if key_value in my_dict_voltage:
            value = my_dict_voltage[key_value]
            print(f"Key: {key_value}, Value: {value}")
        else:
            print(f"Key: {key_value} not found in JSON")

def find_csv_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.cex'):
            base_name = os.path.splitext(filename)[0]
            csv_filename = base_name + '.csv'
            csv_filepath = os.path.join(folder_path, csv_filename)
            cex_filepath = os.path.join(folder_path, filename)
            if os.path.exists(csv_filepath):
                df1 = read_cex(cex_filepath)
                df2 = creat_csv_dict(csv_filepath)
                hebing(df1, df2)

def change_cex(file, new_data, add):
    with open(file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
        identifier = b'\xbb\xbb\xff\xff\x13\x00'
        header = mm.find(identifier) + 16
        mm.seek(header + add * 16)
        mm.write(unhexlify(new_data))
        mm.close()

def str_to_bin(file):
    with open(file, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
        identifier = b'\xbb\xbb\xff\xff\x13\x00'
        header = mm.find(identifier) + 16000
        mm.seek(header)
        byte = mm.read(16)
        line_idb = int.from_bytes(byte[8:12], byteorder='little')
        print(line_idb)


if '__name__' == '__main__':
    read_cex("example.cex")