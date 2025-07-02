import re
import os
import argparse


def get_file_context(file_path):
    with open(file_path, 'r') as f:
        context = f.read()
    return context

class CheckTests:
    def __init__(self, test_path, test_out_path):
        self.test_path = test_path
        self.test_out_path = test_out_path
        self.context = get_file_context(self.test_path)
        self.log = get_file_context(self.test_out_path)
        self.commands = self.get_commands()

    def get_commands(self):
        commands = []
        lines = self.context.splitlines()
        for line in lines:
            if line.startswith("##PACKSPEC##"):
                commands.append(line[len("##PACKSPEC##"):].strip())
        return commands

    def check_commands(self):
        check_num = 0
        for command in self.commands:
            if command.startswith("EXIST:"):
                exist_context = command[len("EXIST:"):].strip()
                if exist_context not in self.log:
                    print(f"Error: '{exist_context}' not found in {self.test_out_path}")
                    exit(1)
                else:
                    check_num += 1
            elif re.match(r'EXIST\*(\d+):', command):
                match_result = re.match(r'EXIST\*(\d+):', command)
                if match_result:
                    number = match_result.group(1)
                    exist_context = command[len(f'EXIST*{number}:'):].strip()
                    count = self.log.count(exist_context)
                    if count != int(number):
                        print(f"Error: Expected to find {number} occurrences of '{exist_context}' in " +
                            f"{os.path.basename(self.test_out_path)}, but found {count} occurrences")
                        exit(1)
                    else:
                        check_num += 1
        return check_num

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='检查测试文件和输出日志')
    parser.add_argument('--test_path', type=str, required=True, help='测试文件的路径')
    parser.add_argument('--test_out_path', type=str, required=True, help='测试输出日志的路径')

    args = parser.parse_args()
    test_path = args.test_path
    test_out_path = args.test_out_path

    ct = CheckTests(test_path, test_out_path)
    check_num = ct.check_commands()
    GREEN = '\033[92m'
    END = '\033[0m'
    print(f"{GREEN}[PASS]{END} All {check_num} Check passed")
    exit(0)
