import random
import sys
from pathlib import Path
from sys import argv
from typing import Any

from server import check_hostname

local_IP = '127.0.0.1'  # local
FORMAT = 'utf-8'


# TODO: parse args
def parse_args(args):
    """
     Return master file path and directory path for single configuration files.
    """
    # check number of arguments
    if len(args) != 2:
        print('INVALID ARGUMENTS')
        sys.exit()

    master_file_path = args[0]
    single_files_dir_path = args[1]

    return master_file_path, single_files_dir_path


def load_config(fobj):
    try:  # extract file and read it
        with open(fobj, 'r') as filename:
            lines = filename.readlines()
    except IOError:
        print('INVALID MASTER')
        sys.exit()

    # check if the file has only one line containing the port of the server
    if len(lines) == 1:
        print('INVALID MASTER')
        sys.exit()
    # extract each information from the file
    # Step 1: extract port of server and check invalid port number
    try:
        port_of_server = int(lines[0].strip())
        if not (1024 <= port_of_server <= 65535):
            print("INVALID MASTER")
            sys.exit()
    except ValueError:
        print('INVALID MASTER')
        sys.exit()

        # create a dictionary to attach each port number of a domain
    record = {}
    # loop through the list containing all information we extracted before except the first line
    for each_line in lines[1:]:
        # split the line and check if it's valid
        parts = each_line.strip().split(',')
        if len(parts) != 2:
            print('INVALID MASTER')
            sys.exit()

        domain, port_identifier = parts
        # check invalid domain and partial domain
        if not check_hostname(domain) or len(domain.split('.')) < 3:
            print('INVALID MASTER')
            sys.exit()
        try:  # check invalid port identifier
            if not (1024 <= int(port_identifier) <= 65535):
                print('INVALID MASTER')
                sys.exit()
        except ValueError:
            print('INVALID MASTER')
            sys.exit()

        # check for contradicting records
        if domain in record:  # access to dictionary
            if record.get(domain) != int(port_identifier):  # check if the domain get 2 port then print Invalid
                print('INVALID MASTER')
                sys.exit()

        # set the pair < key, value > in dictionary with each domain and port identifier
        record[domain] = int(port_identifier)

        # return the dictionary as the library contains address of all books and the port of the server
    return record, port_of_server


def validate_master_file(file: str) -> tuple[dict[Any, int], int]:
    """
    Check if the master file is existing and is valid configuration file
    """
    master_file = Path(file)
    if not master_file.exists():
        print('INVALID MASTER')
        sys.exit()

    # read master_file and check if it is readable or not
    return load_config(master_file)


def validate_directory_path(file: str):
    # check existence of dir_path
    dir_path = Path(file)
    if not dir_path.is_dir() or not dir_path.exists():
        return False

    # check the directory can be written or not
    filepath = dir_path / 'text.txt'

    try:
        with open(filepath, 'w') as f_obj:
            pass
        # If successful, remove the temporary file
        filepath.unlink()
    except IOError:
        return False

    # if we can write to dir
    return True


def separate_domain(domain: str) -> tuple:
    """
    Split a domain into its subdomain, domain, and TLD parts.
    """
    each_part = domain.split('.')
    # if it is partial domain
    if len(each_part) < 3:
        return None, each_part[0], each_part[-1]

    # if full domain
    return each_part[0], each_part[-2], each_part[-1]


def generate_random_port() -> int:
    """
    Generate a random port number.
    """
    return random.randint(1024, 65535)  # valid port in this range


def generate_single_config_file(single_files_dir_path: str, record, root_port):
    # Validate directory path
    if not validate_directory_path(single_files_dir_path):
        return False

    # Create dictionaries to store top level domain and domains
    dict_top_level_domains = {}
    domains = {}

    # Use the record to extract subdomain, domain, tld, and port
    for full_domain, port in record.items():
        subdomain, domain, tld = separate_domain(full_domain)
        if tld not in dict_top_level_domains:
            # hold that tld name in a dictionary and create a random port for that tld name like com, 3223
            dict_top_level_domains[tld] = generate_random_port()
        domain_name = f"{domain}.{tld}"
        if domain_name not in domains:
            # hold that domain name into dictionary by getting a new random port
            domains[domain_name] = generate_random_port()

    # Write the root-conf file
    file_root = Path(single_files_dir_path).joinpath("root-conf")
    with open(file_root, 'w') as f_obj:
        # write the first line with the port number that belong to port of server
        f_obj.write(str(root_port) + '\n')
        for tld, port_of_tld in dict_top_level_domains.items():
            # eg com,1024
            f_obj.write(f"{tld}, {port_of_tld}\n")

    # Write the tld-*.conf files
    for tld, port_of_tld in dict_top_level_domains.items():
        tld_file = Path(single_files_dir_path).joinpath(f'tld-{tld}.conf')
        with open(tld_file, 'w') as f_obj:
            # write the first line with the port number that belong to tld server
            f_obj.write(str(port_of_tld) + '\n')
            for domain, domain_port in domains.items():
                # write to tld file each domain that end with tld
                if domain[-len(tld):] == tld:
                    f_obj.write(f"{domain}, {domain_port}" + '\n')

    # Write the auth-*.conf files
    for domain, domain_port in domains.items():
        auth_file = Path(single_files_dir_path).joinpath(f'auth-{domain.split(".")[0]}.conf')
        with open(auth_file, 'w') as f_obj:
            # write the first line with the port number that belong to authoritative server
            f_obj.write(str(domain_port) + '\n')
            for full_domain, port_of_full_domain in record.items():
                if full_domain[-len(domain):] == domain:
                    # eg: www.google.com and the last part is com
                    f_obj.write(f"{full_domain}, {port_of_full_domain}" + '\n')


def main(args: list[str]) -> None:
    # 1. Parse command-line arguments
    master_file_path, single_files_dir_path = parse_args(args)

    # 2. Validate the master configuration and directory
    record, port_of_server = validate_master_file(master_file_path)
    if not validate_directory_path(single_files_dir_path):
        print("NON-WRITABLE SINGLE DIR")
        sys.exit()

    # 3. Generate single configurations
    generate_single_config_file(single_files_dir_path, record, port_of_server)


if __name__ == "__main__":
    main(argv[1:])