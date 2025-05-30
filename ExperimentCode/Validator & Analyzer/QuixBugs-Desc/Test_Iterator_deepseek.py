import json
import os
import re
from openai import OpenAI
from test import process_log, run_tests_and_process_log
import chardet  # 用于检测文件编码

# 初始化 OpenAI 客户端
client = OpenAI(api_key="Your api_key", base_url="https://api.deepseek.com")

# 文件路径
result_path = "C:\\Users\\15154\\Desktop\\testcase\\result\\result.json"
dataset_path = "C:\\Users\\15154\\Desktop\\testcase\\quixbugs.json"
output_dir = "D:\\QuixBugs-master\\QuixBugs-master\\java_testcases\\junit"
command = "cd /d D:\\QuixBugs-master\\QuixBugs-master && gradlew test"

# 最大迭代次数
max_iterations_compile = 5  # 编译错误的最大迭代次数
max_iterations_test = 5     # 测试失败的最大迭代次数

def detect_file_encoding(file_path):
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        print(f"检测文件 {file_path} 编码: {encoding} (置信度: {confidence})")
        return encoding
    except Exception as e:
        print(f"检测文件编码失败: {e}")
        return 'utf-8'  # 默认使用 UTF-8

def read_file_with_encoding(file_path):
    """尝试以不同编码读取文件"""
    encodings = ['utf-8', 'gbk', 'latin1']
    detected_encoding = detect_file_encoding(file_path)
    encodings = [detected_encoding] + [e for e in encodings if e != detected_encoding]

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            print(f"成功以 {encoding} 编码读取文件: {file_path}")
            return content, encoding
        except UnicodeDecodeError as e:
            print(f"以 {encoding} 编码读取 {file_path} 失败: {e}")
    raise UnicodeDecodeError(f"无法读取文件 {file_path}，尝试了编码: {encodings}", b"", 0, 0, "")

def analyze_results(model_name="deepseek-chat"):
    """
    分析测试结果并尝试修复编译或测试失败。

    参数:
        model_name (str): 使用的 DeepSeek 模型名称，默认为 deepseek-chat
    """
    # 检查文件和目录
    if not os.path.exists(dataset_path):
        print(f"数据集文件不存在: {dataset_path}")
        return
    if not os.path.exists(output_dir):
        print(f"测试用例目录不存在: {output_dir}")
        return
    if not os.path.exists(result_path):
        print(f"结果文件不存在: {result_path}")
        return

    # 读取 quixbugs.json
    try:
        content, encoding = read_file_with_encoding(dataset_path)
        quixbugs_data = json.loads(content)
        print(f"JSON 数据条目数: {len(quixbugs_data)}")
    except Exception as e:
        print(f"读取数据集文件失败: {e}")
        return

    # 构建 class_name -> {summary, method_body} 映射
    class_info_map = {}
    for entry in quixbugs_data:
        under_test = entry.get("Under_test_method", {})
        class_name = under_test.get("Class_name", "").strip()
        summary = under_test.get("Summary", "").strip()
        method_body = under_test.get("Method_body", "").strip()
        if class_name:
            class_info_map[class_name] = {"Summary": summary, "Method_body": method_body}
    print(f"class_info_map 键数: {len(class_info_map)}")

    # 读取 result.json
    try:
        content, encoding = read_file_with_encoding(result_path)
        result_data = json.loads(content)
        print(f"result.json 类名数: {len(result_data)}")
    except Exception as e:
        print(f"读取 result.json 失败: {e}")
        return

    # 记录已修复的类名
    repaired_classes = set()

    # 处理 result.json 中的每个类名
    for test_class_name in list(result_data.keys()):
        if test_class_name in repaired_classes:
            print(f"[跳过] {test_class_name} 已修复，跳过")
            continue

        # 提取 Class_name（去掉 _Test 后缀）
        class_name = test_class_name.replace("_Test", "")
        print(f"\n[开始处理] 测试类: {test_class_name}, 类名: {class_name}")

        # 检查 class_name 是否在 class_info_map 中
        if class_name not in class_info_map:
            print(f"[错误] {class_name} 不在 quixbugs.json 中，跳过")
            result_data[test_class_name] = ["Class not found in quixbugs.json"]
            repaired_classes.add(test_class_name)
            continue

        info = class_info_map[class_name]
        testcase_path = os.path.join(output_dir, f"{test_class_name}.java")

        # 检查测试文件是否存在
        if not os.path.exists(testcase_path):
            print(f"测试文件不存在: {testcase_path}")
            result_data[test_class_name] = ["Test file does not exist"]
            repaired_classes.add(test_class_name)
            continue

        # 执行修复逻辑
        iteration = 0
        compile_status = 0  # 初始假设编译失败
        test_status = 0    # 初始假设测试失败

        while (compile_status != 1 or test_status != 1) and iteration < (max_iterations_compile if compile_status == 0 else max_iterations_test):
            try:
                print(f"[迭代 {iteration + 1}] 开始修复 {test_class_name}")

                # 读取测试用例文件
                try:
                    testcase_content, file_encoding = read_file_with_encoding(testcase_path)
                except UnicodeDecodeError as e:
                    print(f"读取测试文件失败: {e}")
                    result_data[test_class_name] = ["Failed to read test file due to encoding error"]
                    repaired_classes.add(test_class_name)
                    break

                # 执行编译 & 测试
                results = run_tests_and_process_log()
                print(f"测试结果: {results}")

                # 检查测试结果
                failed_tests = results.get(test_class_name, [])
                compile_status = 1 if not any("compile error" in str(test).lower() for test in failed_tests) else 0
                test_status = 1 if not failed_tests else 0

                if compile_status == 0:
                    repair_flag = 1  # 编译失败
                    max_iterations = max_iterations_compile
                elif compile_status == 1 and test_status == 0:
                    repair_flag = 2  # 测试失败
                    max_iterations = max_iterations_test
                elif compile_status == 1 and test_status == 1:
                    repair_flag = 3  # 成功
                else:
                    repair_flag = -1  # 无效状态

                if repair_flag == 3:
                    print(f"[成功] {test_class_name}.java 修复成功！")
                    result_data[test_class_name] = []
                    repaired_classes.add(test_class_name)
                    break

                # Step 1: Method_body 分析
                method_analysis_prompt = (
                    "You are a Java testing expert tasked with analyzing a method's control flow and semantic behavior.\n"
                    "Please analyze the following method and provide a detailed breakdown of its branch structure:\n"
                    "1. Identify all conditional branches within loops (e.g., if/else/switch statements, return/break/continue)\n"
                    "2. Identify conditions evaluated after loops (post-loop conditions)\n"
                    "3. Identify implicit branches (default paths or behaviors not explicitly defined in conditionals)\n"
                    "4. Provide a clear semantic description of the method's overall behavior\n"
                    f"[Method Code]\n{info['Method_body']}\n"
                    "[Environment Context]\nJDK 11\n"
                    "Return the analysis in a structured format, listing each branch type separately."
                )

                method_response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a Java testing expert."},
                        {"role": "user", "content": method_analysis_prompt},
                    ],
                    temperature=0
                )
                buggy_method_understanding = method_response.choices[0].message.content.strip()
                print(f"Method 分析结果（前100字符）: {buggy_method_understanding[:100]}...")

                # Step 2: Summary 分析与对比
                summary_analysis_prompt = (
                    "You are a Java testing expert tasked with validating a method's summary against its implementation.\n"
                    "The provided Summary describes the correct, intended behavior of the method. Your task is to:\n"
                    "1. Analyze the Summary to identify the expected branch structure (conditional branches, loop conditions, implicit branches)\n"
                    "2. Compare these expected branches with the Method_body's branch analysis to identify discrepancies\n"
                    "3. If discrepancies exist, assume the Summary is correct and note which branches in Method_body are incorrect or missing\n"
                    f"[Summary]\n{info['Summary']}\n"
                    f"[Method_body Branch Analysis]\n{buggy_method_understanding}\n"
                    "[Environment Context]\nJDK 11"
                )

                summary_response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a Java testing expert."},
                        {"role": "user", "content": summary_analysis_prompt},
                    ],
                    temperature=0
                )
                summary_understanding = summary_response.choices[0].message.content.strip()
                print(f"Summary 分析结果（前100字符）: {summary_understanding[:100]}...")

                # Step 3: 测试修复生成
                repair_prompt = (
                    "You are a Java testing expert tasked with improving test cases to cover all intended method behaviors.\n"
                    "Based on the correct branch structure (from Summary analysis), your tasks are:\n"
                    "1. Analyze the existing test cases to identify which branches from the Summary they cover\n"
                    "2. For branches covered correctly, preserve those test cases\n"
                    "3. For branches not covered or incorrectly tested, generate new test cases that:\n"
                    "   - Cover all missing branches (conditional, loop, implicit)\n"
                    "   - Include boundary cases (null, empty, max values, etc.)\n"
                    "   - Detect flaws identified in the Summary vs. Method_body comparison\n"
                    "   - Have descriptive names and clear assertion messages\n"
                    "   - Are concise and maintain test independence\n"
                    f"[Summary Branch Analysis]\n{summary_understanding}\n"
                    f"[Original Test Code]\n{testcase_content}\n"
                    f"[Environment Context]\nJDK 11 + JUnit 1.4\n"
                    "[Critical Requirements]\n"
                    "1. Return ONLY the corrected .java file content in a code block.\n"
                    "2. Preserve valid test methods and class structure\n"
                    "3. Add new test methods only for missing or incorrect branches"
                )

                repair_response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a professional who writes Java test methods."},
                        {"role": "user", "content": repair_prompt},
                    ],
                    temperature=0
                )
                generated_code = repair_response.choices[0].message.content.strip()
                cleaned_code = re.sub(r"```(java)?", "", generated_code).strip()

                # 保存修复后的测试文件
                try:
                    with open(testcase_path, "w", encoding="utf-8") as f:
                        f.write(cleaned_code)
                    print(f"[保存] 修复后的测试用例保存至：{testcase_path}")
                except UnicodeEncodeError as e:
                    print(f"写入测试文件失败: {e}")
                    result_data[test_class_name] = ["Failed to write test file due to encoding error"]
                    repaired_classes.add(test_class_name)
                    break

                # 更新迭代计数
                iteration += 1

                # 检查修复是否成功
                if compile_status == 1 and test_status == 1:
                    print(f"[成功] {test_class_name}.java 修复成功！")
                    result_data[test_class_name] = []
                    repaired_classes.add(test_class_name)
                    break
                else:
                    print(f"[迭代 {iteration}] 修复仍未通过测试，继续迭代...")
                    result_data[test_class_name] = failed_tests

            except Exception as e:
                print(f"[错误] 在处理 {test_class_name} 时发生异常: {str(e)}")
                result_data[test_class_name] = ["Exception: " + str(e)]
                repaired_classes.add(test_class_name)
                break

        # 如果迭代结束仍未修复，记录失败测试用例并标记为已修复
        if test_class_name not in repaired_classes:
            print(f"[失败] {test_class_name}.java 达到最大迭代次数 {max_iterations_compile if compile_status == 0 else max_iterations_test}，仍未修复")
            result_data[test_class_name] = failed_tests
            repaired_classes.add(test_class_name)

    # 保存最终结果
    try:
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)
        print("所有类处理完成，结果已保存。")
    except Exception as e:
        print(f"保存最终结果失败: {e}")

if __name__ == "__main__":
    analyze_results()