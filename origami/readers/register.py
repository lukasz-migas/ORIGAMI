def pause():
    print("\nPress enter to continue.")
    input()
    return


def register_interfaces():
    print("Checking for access to MS data formats...")

    # Standard library imports
    import ctypes

    assert ctypes.windll.shell32.IsUserAnAdmin(), "register_interfaces() must be run with administrator privileges!"
    # Standard library imports
    import os
    import sys
    import glob
    import subprocess
    from collections import defaultdict

    # Third-party imports
    from win32com.client import Dispatch

    interface_module = {"RawReader.dll": "RAW"}
    interface_module_paths = {"RawReader.dll": os.path.join(os.path.dirname(__file__), "thermo", "RawReader.dll")}
    interface_guids = {"RAW": "{10729396-43ee-49e5-aa07-85f02292ac70}"}

    os_bit = ""
    if sys.maxsize > 2 ** 32:
        os_bit = "64"

    try:
        net_directory = sorted(glob.glob("c:/Windows/Microsoft.NET/Framework%s/v[34]*/RegAsm.exe" % os_bit))[-1]
    except IndexError:
        message = (
            ".NET version 3 or higher not found; the free .NET redistributable can be found at: "
            "http://www.microsoft.com/en-us/download/details.aspx?id=17718"
        )
        print(message)
        pause()
        return 1

    before_checks = {}
    for file_type, guid in list(interface_guids.items()):
        try:
            Dispatch(guid)
            before_checks[file_type] = True
        except:
            before_checks[file_type] = False

    # dll_found = {}
    # for directory in sys.path + [os.path.dirname(sys.executable)]:
    #     if len(os.path.abspath(directory)) <= 3:  # Searching from base directory is unwise.
    #         print(("Not searching from %s" % directory))
    #         continue
    #     for path, names, files in os.walk(directory):
    #         # print path
    #         for filename in files:
    #             if (filename in list(interface_module.keys())) and (not filename in list(dll_found.keys())):
    #                 dll_found[filename] = os.path.join(path, filename)
    #                 if len(dll_found) == len(interface_module):
    #                     break

    register_results = defaultdict(int)
    for filename in list(interface_module.keys()):
        print(("\n\n" + filename + "\n"))
        try:
            dllpath = interface_module_paths[filename]
            ret = subprocess.call([net_directory, dllpath, "/tlb", "/codebase"])
            register_results[interface_module[filename]] |= ret
        except KeyError:
            register_results[interface_module[filename]] = "No .DLL"

    after_checks = {}
    for file_type, guid in list(interface_guids.items()):
        try:
            Dispatch(guid)
            after_checks[file_type] = True
        except Exception as err:
            after_checks[file_type] = False
            print(err)

    print("Registration operations completed.\nResults: \n")
    print("File Type\tRegistered Before\tRegAsm Return Code\tRegistered Now")
    for file_type in list(interface_guids.keys()):
        print(
            (
                "{0}\t\t{1}\t\t{2}\t\t\t{3}".format(
                    file_type, before_checks[file_type], register_results[file_type], after_checks[file_type]
                )
            )
        )
    return 0


if __name__ == "__main__":
    register_interfaces()
