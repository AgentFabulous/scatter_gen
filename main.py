import re


def trim_hex(hex_str):
    return hex(int(hex_str, 16))


def find_key(dictionary, search_string):
    for key, value_list in dictionary.items():
        if search_string in value_list:
            return key
    return None


def operation_type(name):
    operation = {
        "BINREGION": ["nvram"],
        "INVISIBLE": [
            "pgpt",
            "boot_para",
            "para",
            "expdb",
            "frp",
            "nvdata",
            "md_udc",
            "metadata",
            "seccfg",
            "sec1",
        ],
        "PROTECTED": [
            "nvcfg",
            "protect1",
            "protect2",
            "persist",
            "proinfo",
        ],
        "RESERVED": [
            "otp",
            "flashinfo",
            "sgpt",
        ],
    }
    ret = find_key(operation, name)
    if ret is None:
        if name.endswith("_b"):
            return "INVISIBLE"
        else:
            return "UPDATE"
    return ret


def get_type(name):
    ext4 = [
        "nvcfg",
        "nvdata",
        "protect1",
        "protect2",
        "persist",
        "userdata",
    ]
    if name in ext4:
        return "EXT4_IMG"
    else:
        return "NORMAL_ROM"


def trim_slot_suffix(string):
    if string.endswith(("_a", "_b")):
        return string[:-2]
    else:
        return string


def get_filename(name):
    filename_none = [
        "pgpt",
        "boot_para",
        "para",
        "expdb",
        "frp",
        "nvcfg",
        "nvdata",
        "md_udc",
        "metadata",
        "protect1",
        "protect2",
        "seccfg",
        "persist",
        "sec1",
        "proinfo",
        "nvram",
        "otp",
        "flashinfo",
        "sgpt",
    ]
    if name == "logo":
        return "logo.bin"
    if name.endswith("_b") or name in filename_none:
        return "NONE"
    else:
        return "{}.img".format(trim_slot_suffix(name))


def get_download(name):
    download = [
        "preloader",
        "logo",
        "md1img",
        "spmfw",
        "scp",
        "sspm",
        "gz",
        "lk",
        "boot",
        "dtbo",
        "tee",
        "vbmeta",
        "vbmeta_system",
        "vbmeta_vendor",
        "super",
        "userdata",
        "init_boot",
        "vendor_boot",
    ]
    if name.endswith("_b"):
        return "false"
    part_name = trim_slot_suffix(name)
    if part_name in download:
        return "true"
    else:
        return "false"


def get_upgradable(name):
    upgradable = [
        "preloader",
        "md1img",
        "spmfw",
        "scp",
        "sspm",
        "gz",
        "lk",
        "boot",
        "dtbo",
        "tee",
        "super",
        "vbmeta",
        "vbmeta_system",
        "vbmeta_vendor",
        "init_boot",
        "vendor_boot",
    ]
    part_name = trim_slot_suffix(name)
    if part_name in upgradable:
        return "true"
    else:
        return "false"


def get_empty_boot(name):
    empty_boot = [
        "logo",
        "lk",
        "tee"
    ]
    if name.endswith("_b"):
        return "false"
    part_name = trim_slot_suffix(name)
    if part_name in empty_boot:
        return "true"
    else:
        return "false"


# Function to generate the output format from the GPT table
def generate_output_format(gpt_table):
    output_format = """############################################################################################################
#
#  General Setting
#
############################################################################################################
- general: MTK_PLATFORM_CFG
  info: 
    - config_version: V1.1.2
      platform: MT6765
      project: k65
      storage: EMMC
      boot_channel: MSDC_0
      block_size: 0x20000
############################################################################################################
#
#  EMMC Layout Setting
#
############################################################################################################
- partition_index: SYS0
  partition_name: preloader
  file_name: preloader.bin
  is_download: true
  type: SV5_BL_BIN
  linear_start_addr: 0x0
  physical_start_addr: 0x0
  partition_size: 0x40000
  region: EMMC_BOOT1_BOOT2
  storage: HW_STORAGE_EMMC
  boundary_check: true
  is_reserved: false
  operation_type: BOOTLOADERS
  is_upgradable: true
  empty_boot_needed: false
  combo_partsize_check: false
  reserve: 0x00

- partition_index: SYS1
  partition_name: pgpt
  file_name: NONE
  is_download: false
  type: NORMAL_ROM
  linear_start_addr: 0x0
  physical_start_addr: 0x0
  partition_size: 0x8000
  region: EMMC_USER
  storage: HW_STORAGE_EMMC
  boundary_check: true
  is_reserved: false
  operation_type: INVISIBLE
  is_upgradable: false
  empty_boot_needed: false
  combo_partsize_check: false
  reserve: 0x00"""

    partition_template = """

- partition_index: {index}
  partition_name: {name}
  file_name: {filename}
  is_download: {download}
  type: {type}
  linear_start_addr: {start}
  physical_start_addr: {start}
  partition_size: {size}
  region: EMMC_USER
  storage: HW_STORAGE_EMMC
  boundary_check: true
  is_reserved: {reserved}
  operation_type: {operation}
  is_upgradable: {upgradable}
  empty_boot_needed: {empty_boot}
  combo_partsize_check: false
  reserve: 0x00"""

    last_index = 0
    # Extract partition information and format output
    for index, line in enumerate(gpt_table.strip().split('\n'), start=2):
        last_index = index
        name, rest = line.split(': ', 1)
        offset = re.search(r'Offset (0x[0-9a-fA-F]+)', rest).group(1)
        length = re.search(r'Length (0x[0-9a-fA-F]+)', rest).group(1)

        output_format += partition_template.format(
            index=f'SYS{index}',
            name=name,
            start=trim_hex(offset),
            size=trim_hex(length),
            type=get_type(name),
            operation=operation_type(name),
            upgradable=get_upgradable(name),
            download=get_download(name),
            filename=get_filename(name),
            empty_boot=get_empty_boot(name),
            reserved= "true" if operation_type(name) == "RESERVED" else "false",
        )

    sgpt = f"""

- partition_index: SYS{last_index + 1}
  partition_name: sgpt
  file_name: NONE
  is_download: false
  type: NORMAL_ROM
  linear_start_addr: 0xFFFF0000
  physical_start_addr: 0xFFFF0000
  partition_size: 0x8000
  region: EMMC_USER
  storage: HW_STORAGE_EMMC
  boundary_check: false
  is_reserved: true
  operation_type: RESERVED
  is_upgradable: false
  empty_boot_needed: false
  combo_partsize_check: false
  reserve: 0x00
"""
    output_format += sgpt
    return output_format


# Function to write the output to a file
def write_to_file(output_format, filename="MT6765_Android_scatter.txt"):
    with open(filename, 'w') as file:
        file.write(output_format)


# Main function to accept GPT table as input and write to file
def main():
    print("Please input the GPT table. Press Enter on an empty line to finish.")
    gpt_table_lines = []
    while True:
        line = input()
        if not line:
            break
        gpt_table_lines.append(line)
    gpt_table = '\n'.join(gpt_table_lines)
    output_format = generate_output_format(gpt_table)
    output_format += '\n'
    write_to_file(output_format)
    print(f"Output written to MT6765_Android_scatter.txt")


if __name__ == "__main__":
    main()
