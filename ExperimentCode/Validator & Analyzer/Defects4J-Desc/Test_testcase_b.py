import json
import os
import shutil
import subprocess
import signal

# 常量定义保持不变
json_file_path = "/home/zyx/Desktop/Buggy_Tester/data_newest.json"
combined_output_path = "/home/zyx/Desktop/Buggy_Tester/log/deepseek/result_deepseek_5.json"

os.makedirs(os.path.dirname(combined_output_path), exist_ok=True)

def process_projects():
    combined_results = []
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取 JSON 文件失败：{e}")
        return None

    for item in data:
        under_test_method = item.get("Under_test_method", {})
        sub_project_name = under_test_method.get("sub_project_name", "")
        class_name = under_test_method.get("Class_name", "")
        Test_name = f"{class_name}Test"

        if sub_project_name not in ["chart", "cli", "closure", "codec", "collections",
                                    "compress", "csv", "gson", "jacksoncore",
                                    "jacksondatabind", "jacksonxml", "jsoup", "jxpath",
                                    "lang", "math", "mockito", "time"]:
            continue

        project_path = under_test_method.get("project_path", "")
        if not project_path:
            print(f"项目路径为空，跳过：{under_test_method}")
            continue

        parts = project_path.split('/')
        num = parts[2].split('_')[1]

        test_flag = 0
        command = ""
        log_output = ""

        try:
            # 根据 sub_project_name 设置路径，替换 _fixed 为 _buggy
            if sub_project_name == "chart":
                chart_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():  
                        chart_index = i
                        break
                if chart_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[chart_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/chart_{num}"
                ori_test_dir = f"/tmp/chart_{num}_buggy/tests/{package_path}"
            elif sub_project_name == "cli":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                if int(num) < 30:
                    test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/cli_{num}"
                    ori_test_dir = f"/tmp/cli_{num}_buggy/src/test/{package_path}"
                elif int(num) > 30:
                    test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/cli_{num}"
                    ori_test_dir = f"/tmp/cli_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "closure":
                com_index = -1
                for i, part in enumerate(parts):
                    if "com" in part.lower():
                        com_index = i
                        break
                if com_index == -1:
                    print(f"路径中未找到 'com'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[com_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/closure_{num}"
                ori_test_dir = f"/tmp/closure_{num}_buggy/test/{package_path}"
            elif sub_project_name == "codec":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                if int(num) < 15:
                    test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/codec_{num}"
                    ori_test_dir = f"/tmp/codec_{num}_buggy/src/test/{package_path}"
                elif int(num) >= 15:
                    test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/codec_{num}"
                    ori_test_dir = f"/tmp/codec_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "collections":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/collections_{num}"
                ori_test_dir = f"/tmp/collections_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "compress":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/compress_{num}"
                ori_test_dir = f"/tmp/compress_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "csv":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/csv_{num}"
                ori_test_dir = f"/tmp/csv_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "gson":
                com_index = -1
                for i, part in enumerate(parts):
                    if "com" in part.lower():
                        com_index = i
                        break
                if com_index == -1:
                    print(f"路径中未找到 'com'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[com_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/gson_{num}"
                ori_test_dir = f"/tmp/gson_{num}_buggy/gson/src/test/java/{package_path}"
            elif sub_project_name == "jacksoncore":
                com_index = -1
                for i, part in enumerate(parts):
                    if "com" in part.lower():
                        com_index = i
                        break
                if com_index == -1:
                    print(f"路径中未找到 'com'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[com_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jacksoncore_{num}"
                ori_test_dir = f"/tmp/jacksoncore_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "jacksondatabind":
                com_index = -1
                for i, part in enumerate(parts):
                    if "com" in part.lower():
                        com_index = i
                        break
                if com_index == -1:
                    print(f"路径中未找到 'com'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[com_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jacksondatabind_{num}"
                ori_test_dir = f"/tmp/jacksondatabind_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "jacksonxml":
                com_index = -1
                for i, part in enumerate(parts):
                    if "com" in part.lower():
                        com_index = i
                        break
                if com_index == -1:
                    print(f"路径中未找到 'com'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[com_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jacksonxml_{num}"
                ori_test_dir = f"/tmp/jacksonxml_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "jsoup":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jsoup_{num}"
                ori_test_dir = f"/tmp/jsoup_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "lang":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                if int(num) < 35:
                    test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/lang_{num}"
                    ori_test_dir = f"/tmp/lang_{num}_buggy/src/test/java/{package_path}"
                elif int(num) > 35:
                    test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/lang_{num}"
                    ori_test_dir = f"/tmp/lang_{num}_buggy/src/test/{package_path}"
            elif sub_project_name == "math":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                if int(num) < 84:
                    test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/math_{num}"
                    ori_test_dir = f"/tmp/math_{num}_buggy/src/test/java/{package_path}"
                elif int(num) > 84:
                    test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/math_{num}"
                    ori_test_dir = f"/tmp/math_{num}_buggy/src/test/{package_path}"
            elif sub_project_name == "mockito":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/mockito_{num}"
                ori_test_dir = f"/tmp/mockito_{num}_buggy/test/{package_path}"
            elif sub_project_name == "time":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/time_{num}"
                ori_test_dir = f"/tmp/time_{num}_buggy/src/test/java/{package_path}"
            elif sub_project_name == "jxpath":
                org_index = -1
                for i, part in enumerate(parts):
                    if "org" in part.lower():
                        org_index = i
                        break
                if org_index == -1:
                    print(f"路径中未找到 'org'，跳过：{project_path}")
                    continue
                package_path = '/'.join(parts[org_index:-1])
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jxpath_{num}"
                ori_test_dir = f"/tmp/jxpath_{num}_buggy/src/test/{package_path}"

            os.makedirs(ori_test_dir, exist_ok=True)

            if os.path.exists(test_case_dir):
                for file_name in os.listdir(test_case_dir):
                    src_file = os.path.join(test_case_dir, file_name)
                    dst_file = os.path.join(ori_test_dir, file_name)
                    if os.path.isfile(src_file):
                        shutil.copy2(src_file, dst_file)
                print(f"已将 {test_case_dir} 中的文件复制到 {ori_test_dir}")
                test_flag = 1
            else:
                print(f"{test_case_dir} 不存在，跳过复制")
                continue

            # 修改命令中的路径为 _buggy
            command = f"cd /tmp/{sub_project_name}_{num}_buggy && defects4j compile && defects4j test"
            try:
                process = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    capture_output=True,
                    timeout=180
                )
                log_output = f"Command: {command}\nSTDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}\n"
                if process.returncode != 0:
                    print(f"命令执行失败，退出码：{process.returncode}")
            except subprocess.TimeoutExpired as e:
                log_output = f"Command: {command}\nTimeout Error: Execution exceeded 180 seconds\n"
                print(f"测试 {sub_project_name}_{num} 超时（超过180秒），已终止")
                process = e

        except Exception as e:
            log_output += f"执行过程中出错：{e}\n"
            print(f"处理 {sub_project_name}_{num} 时出错：{e}")

        compile_result, test_result = analyze_test_results(log_output, Test_name)
        result = {
            "sub_project_name": sub_project_name,
            "num": num,
            "name": Test_name,
            "Compile": compile_result,
            "Test": test_result,
            "project_path": project_path,
            "test_case_dir": test_case_dir,
            "ori_test_dir": ori_test_dir,
            "log": log_output,
            "success": test_flag == 1 and getattr(process, 'returncode', -1) == 0
        }
        combined_results.append(result)

    try:
        with open(combined_output_path, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=4, ensure_ascii=False)
        print(f"所有结果已保存到 {combined_output_path}")
    except Exception as e:
        print(f"保存结果失败：{e}")

    return combined_results

def analyze_test_results(log: str, name: str) -> (int, int):
    if "Timeout Error" in log:
        return 0, 0

    if "(compile.tests)................................................ FAIL" in log:
        return 0, 0

    if "Failing tests:" in log:
        start = log.index("Failing tests:")
        end = log.find("\n\n", start) if "\n\n" in log[start:] else len(log)
        failed_tests = set()
        for line in log[start:end].split("\n"):
            if "::" in line:
                test_class = line.split("::")[0].split(".")[-1]
                failed_tests.add(test_class)
        if name in failed_tests:
            return 1, 0

    return 1, 1

def main():
    print("开始处理所有项目...")
    results = process_projects()
    if results:
        success_count = sum(1 for r in results if r.get("success", False))
        print(f"处理完成！成功: {success_count}, 失败: {len(results) - success_count}")
    else:
        print("项目处理失败或无数据")

    print("\n程序执行完成！")

if __name__ == "__main__":
    main()
