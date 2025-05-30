import json
import os
import subprocess
import shutil

# 定义常量
result_json_path = "/home/zyx/Desktop/DISTINCT/log/result.json"
output_json_path = "/home/zyx/Desktop/DISTINCT/log/coverage.json"

# 确保输出目录存在
os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

def clean_test_dir(ori_test_dir, name, test_case_dir):
    """
    清理 ori_test_dir 下的 .java 文件，仅保留从 test_case_dir 复制的 name.java，保留文件夹
    
    Args:
        ori_test_dir: 目标测试目录路径
        name: 测试用例名称（对应 name.java 文件）
        test_case_dir: 测试用例源目录路径
    
    Returns:
        bool: 是否成功清理
    """
    if not os.path.exists(ori_test_dir):
        print(f"目录 {ori_test_dir} 不存在")
        return False
    
    target_file = f"{name}.java"
    source_file = os.path.join(test_case_dir, target_file)
    
    try:
        # 复制 test_case_dir 中的 name.java 到 ori_test_dir
        if os.path.exists(source_file):
            shutil.copy2(source_file, os.path.join(ori_test_dir, target_file))
            print(f"已从 {source_file} 复制 {target_file} 到 {ori_test_dir}")
        else:
            print(f"源文件 {source_file} 不存在")
            return False
        
        # 清理 ori_test_dir 中其他 .java 文件
        for file_name in os.listdir(ori_test_dir):
            file_path = os.path.join(ori_test_dir, file_name)
            # 只处理 .java 文件，不删除文件夹，且不删除目标文件
            if os.path.isfile(file_path) and file_name.endswith(".java") and file_name != target_file:
                os.remove(file_path)
                print(f"已删除 {file_path}")
        print(f"已清理 {ori_test_dir}，仅保留 {target_file}")
        return True
    except Exception as e:
        print(f"清理 {ori_test_dir} 失败：{e}")
        return False

def run_coverage(sub_project_name, num):
    """
    执行 defects4j coverage 命令并返回日志
    
    Args:
        sub_project_name: 项目名称（如 lang, chart 等）
        num: 项目编号
    
    Returns:
        str: 执行日志（包括命令、标准输出和错误输出）
    """
    command = f"cd /tmp/{sub_project_name}_{num}_fixed && defects4j coverage"
    log_output = ""
    try:
        process = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=1200  # 设置 180 秒超时
        )
        log_output = (
            f"Command: {command}\n"
            f"STDOUT:\n{process.stdout}\n"
            f"STDERR:\n{process.stderr}\n"
            f"{'-' * 50}\n"
        )
        if process.returncode != 0:
            print(f"命令执行失败，退出码：{process.returncode}")
            print(f"错误详情:\n{process.stderr}")
    except subprocess.TimeoutExpired:
        log_output = (
            f"Command: {command}\n"
            f"Timeout Error: Execution exceeded 180 seconds\n"
            f"{'-' * 50}\n"
        )
        print(f"覆盖率计算超时：{sub_project_name}_{num}")
    except Exception as e:
        log_output = (
            f"Command: {command}\n"
            f"Error: {str(e)}\n"
            f"{'-' * 50}\n"
        )
        print(f"执行命令出错：{sub_project_name}_{num}, {e}")
    return log_output

def process_coverage():
    """
    读取 result.json，处理 Test == 1 的项目，计算覆盖率并保存结果
    """
    # 读取 result.json
    try:
        with open(result_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取 {result_json_path} 失败：{e}")
        return
    
    # 存储结果
    coverage_results = []
    
    # 遍历每个项目
    for item in data:
        test_status = item.get("Test", -1)
        name = item.get("name", "")
        ori_test_dir = item.get("ori_test_dir", "")
        sub_project_name = item.get("sub_project_name", "")
        num = item.get("num", "")
        test_case_dir = item.get("test_case_dir", "")
        
        # 只处理 Test == 1 的项目
        if test_status != 1:
            continue
        
        print(f"处理项目：{sub_project_name}_{num}, 测试用例：{name}")
        
        # 清理 ori_test_dir，仅保留从 test_case_dir 复制的 name.java
        if not clean_test_dir(ori_test_dir, name, test_case_dir):
            print(f"跳过 {sub_project_name}_{num}，清理测试目录失败")
            continue
        
        # 执行覆盖率计算
        log_output = run_coverage(sub_project_name, num)
        
        # 记录结果
        result = {
            "project": f"{sub_project_name}_{num}",
            "test_case": name,
            "coverage_log": log_output
        }
        coverage_results.append(result)
        print(f"已完成 {sub_project_name}_{num} 的覆盖率计算")
    
    # 保存结果到 JSON 文件
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(coverage_results, f, indent=4, ensure_ascii=False)
        print(f"覆盖率结果已保存到 {output_json_path}")
    except Exception as e:
        print(f"保存结果失败：{e}")

def main():
    print("开始处理覆盖率计算...")
    process_coverage()
    print("覆盖率计算完成！")

if __name__ == "__main__":
    main()
