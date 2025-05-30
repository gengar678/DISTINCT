import json
import os
import shutil
import subprocess
import sys

# 定义常量
result_json_file_path = "/home/zyx/Desktop/Buggy_Tester/log/deepseek/result_deepseek_0.json"
try_json_file_path = "/home/zyx/Desktop/Buggy_Tester/data_newest.json"

def process_single_project(target_path):
    """
    处理单个指定的项目路径，将结果更新到 result.json 中匹配的条目
    
    Args:
        target_path: 要测试的项目路径，例如 "/tmp/lang_14_fixed/src/test/java/org/apache/commons/lang3"
    
    Returns:
        更新后的结果字典，或 None（如果处理失败）
    """
    try:
        # 读取 try.json 文件
        with open(try_json_file_path, 'r', encoding='utf-8') as f:
            try_data = json.load(f)
    except Exception as e:
        print(f"读取 try.json 文件失败：{e}")
        return None

    # 查找匹配的项目
    matched_item = None
    for item in try_data:
        under_test_method = item.get("Under_test_method", {})
        project_path = under_test_method.get("project_path", "")
        if project_path == target_path:
            matched_item = item
            break

    if not matched_item:
        print(f"未在 try.json 文件中找到匹配的路径：{target_path}")
        return None

    # 提取项目信息
    under_test_method = matched_item.get("Under_test_method", {})
    sub_project_name = under_test_method.get("sub_project_name", "")
    class_name = under_test_method.get("Class_name", "")
    Test_name = f"{class_name}Test"

    # 验证项目类型
    valid_projects = ["chart", "cli", "closure", "codec", "collections", "compress", "csv", 
                     "gson", "jacksoncore", "jacksondatabind", "jacksonxml", "jsoup", 
                     "jxpath", "lang", "math", "mockito", "time"]
    
    if sub_project_name not in valid_projects:
        print(f"不支持的项目类型：{sub_project_name}")
        return None

    # 解析项目路径
    parts = target_path.split('/')
    num = parts[2].split('_')[1]  # 提取编号，例如 "lang_14_fixed" 中的 "14"

    # 初始化变量
    test_flag = 0
    command = ""
    log_output = ""

    # 根据项目类型设置路径
    try:
        if sub_project_name == "lang":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            if int(num) < 35:
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/lang_{num}"
                ori_test_dir = f"/tmp/lang_{num}_fixed/src/test/java/{package_path}"
            else:
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/lang_{num}"
                ori_test_dir = f"/tmp/lang_{num}_fixed/src/test/{package_path}"
        
        elif sub_project_name == "chart":
            chart_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():  
                    chart_index = i
                    break
            if chart_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[chart_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/chart_{num}"
            ori_test_dir = f"/tmp/chart_{num}_fixed/tests/{package_path}"
        
        elif sub_project_name == "cli":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            if int(num) < 30:
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/cli_{num}"
                ori_test_dir = f"/tmp/cli_{num}_fixed/src/test/{package_path}"
            elif int(num) > 30:
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/cli_{num}"
                ori_test_dir = f"/tmp/cli_{num}_fixed/src/test/java/{package_path}"

        elif sub_project_name == "closure":
            com_index = -1
            for i, part in enumerate(parts):
                if "com" in part.lower():
                    com_index = i
                    break
            if com_index == -1:
                print(f"路径中未找到 'com'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[com_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/closure_{num}"
            ori_test_dir = f"/tmp/closure_{num}_fixed/test/{package_path}"
        
        elif sub_project_name == "codec":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            if int(num) < 15:
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/codec_{num}"
                ori_test_dir = f"/tmp/codec_{num}_fixed/src/test/{package_path}"
            elif int(num) >= 15:
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/codec_{num}"
                ori_test_dir = f"/tmp/codec_{num}_fixed/src/test/java/{package_path}"
        
        elif sub_project_name == "collections":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/collections_{num}"
            ori_test_dir = f"/tmp/collections_{num}_fixed/src/test/java/{package_path}"
        
        elif sub_project_name == "compress":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/compress_{num}"
            ori_test_dir = f"/tmp/compress_{num}_fixed/src/test/java/{package_path}"
        
        elif sub_project_name == "csv":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/csv_{num}"
            ori_test_dir = f"/tmp/csv_{num}_fixed/src/test/java/{package_path}"
        
        elif sub_project_name == "gson":
            com_index = -1
            for i, part in enumerate(parts):
                if "com" in part.lower():
                    com_index = i
                    break
            if com_index == -1:
                print(f"路径中未找到 'com'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[com_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/gson_{num}"
            ori_test_dir = f"/tmp/gson_{num}_fixed/gson/src/test/java/{package_path}"
        
        elif sub_project_name == "jacksoncore":
            com_index = -1
            for i, part in enumerate(parts):
                if "com" in part.lower():
                    com_index = i
                    break
            if com_index == -1:
                print(f"路径中未找到 'com'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[com_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jacksoncore_{num}"
            ori_test_dir = f"/tmp/jacksoncore_{num}_fixed/src/test/java/{package_path}"
        
        elif sub_project_name == "jacksondatabind":
            com_index = -1
            for i, part in enumerate(parts):
                if "com" in part.lower():
                    com_index = i
                    break
            if com_index == -1:
                print(f"路径中未找到 'com'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[com_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jacksondatabind_{num}"
            ori_test_dir = f"/tmp/jacksondatabind_{num}_fixed/src/test/java/{package_path}"
        
        elif sub_project_name == "jacksonxml":
            com_index = -1
            for i, part in enumerate(parts):
                if "com" in part.lower():
                    com_index = i
                    break
            if com_index == -1:
                print(f"路径中未找到 'com'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[com_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jacksonxml_{num}"
            ori_test_dir = f"/tmp/jacksonxml_{num}_fixed/src/test/java/{package_path}"
        
        elif sub_project_name == "jsoup":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jsoup_{num}"
            ori_test_dir = f"/tmp/jsoup_{num}_fixed/src/test/java/{package_path}"

        elif sub_project_name == "math":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            if int(num) < 84:
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/math_{num}"
                ori_test_dir = f"/tmp/math_{num}_fixed/src/test/java/{package_path}"
            elif int(num) > 84:
                test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/math_{num}"
                ori_test_dir = f"/tmp/math_{num}_fixed/src/test/{package_path}"

        elif sub_project_name == "mockito":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/mockito_{num}"
            ori_test_dir = f"/tmp/mockito_{num}_fixed/test/{package_path}"

        elif sub_project_name == "time":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/time_{num}"
            ori_test_dir = f"/tmp/time_{num}_fixed/src/test/java/{package_path}"

        elif sub_project_name == "jxpath":
            org_index = -1
            for i, part in enumerate(parts):
                if "org" in part.lower():
                    org_index = i
                    break
            if org_index == -1:
                print(f"路径中未找到 'org'，跳过：{target_path}")
                return None
            package_path = '/'.join(parts[org_index:-1])
            test_case_dir = f"/home/zyx/Desktop/Buggy_Tester/ChatBuggyTester_out/jxpath_{num}"
            ori_test_dir = f"/tmp/jxpath_{num}_fixed/src/test/{package_path}"
    
        else:
            print(f"不支持的项目类型：{sub_project_name}")
            return None

        # 确保目标目录存在
        os.makedirs(ori_test_dir, exist_ok=True)

        # 复制测试用例
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
            return None

        # 清理含#的文件
        for file_name in os.listdir(ori_test_dir):
            if "#" in file_name and file_name.endswith(".java"):
                os.remove(os.path.join(ori_test_dir, file_name))

        # 执行测试命令，设置180秒超时
        command = f"cd /tmp/{sub_project_name}_{num}_fixed && defects4j compile && defects4j test"
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
    
    # 构造结果
    result = {
        "sub_project_name": sub_project_name,
        "num": num,
        "name": Test_name,
        "Compile": compile_result,
        "Test": test_result,
        "project_path": target_path,
        "test_case_dir": test_case_dir,
        "ori_test_dir": ori_test_dir,
        "log": log_output,
        "success": test_flag == 1 and getattr(process, 'returncode', -1) == 0
    }

    # 更新 result.json 中匹配的条目
    try:
        with open(result_json_file_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        matched = False
        for item in result_data:
            if item.get("project_path") == target_path:
                item.update({
                    "log": log_output,
                    "Compile": compile_result,
                    "Test": test_result,
                    "success": result["success"],
                    "test_case_dir": test_case_dir,
                    "ori_test_dir": ori_test_dir,
                    "sub_project_name": sub_project_name,
                    "num": num,
                    "name": Test_name
                })
                matched = True
                break
        
        if not matched:
            print(f"未在 result.json 中找到匹配的 project_path: {target_path}")
            return None

        with open(result_json_file_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)
        print(f"结果已更新到 {result_json_file_path} 中 project_path={target_path} 的条目")
    except Exception as e:
        print(f"更新 result.json 文件失败：{e}")
        return None

    return result

def analyze_test_results(log: str, name: str) -> (int, int):
    """
    分析测试日志并返回编译和测试结果
    """
    if "Timeout Error" in log:
        return 0, 0

    if "(compile.tests)................................................ FAIL" in log:
        return 0, 0

    if "Failing tests:" in log:
        start = log.index("Failing tests:")
        end = log.find("\n\n", start) if "\n\n" in log[start:] else len(log)
        failed_tests = [line.split("::")[0].split(".")[-1]
                       for line in log[start:end].split("\n")
                       if "::" in line]
        if name in failed_tests:
            return 1, 0

    return 1, 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
        print(f"开始处理路径：{target_path}")
        result = process_single_project(target_path)
        
        if result:
            if result.get("success", False):
                print("处理成功！")
            else:
                print("处理失败！")
            print(f"Compile: {result['Compile']}, Test: {result['Test']}")
        else:
            print("项目处理失败或路径无效")
    else:
        print("请提供 target_path 参数")
    
    print("\n程序执行完成！")
