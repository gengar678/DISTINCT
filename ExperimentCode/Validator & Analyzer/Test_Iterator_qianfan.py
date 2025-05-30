import json
import os
import re
import qianfan
import time
from collections import defaultdict
from Test_one_Buggy import process_single_project
import uuid

# 设置 Qianfan API 密钥
os.environ["QIANFAN_ACCESS_KEY"] = "Your QIANFAN_ACCESS_KEY"
os.environ["QIANFAN_SECRET_KEY"] = "Your QIANFAN_SECRET_KEY"


def parse_compile_errors(log_content):
    error_num = r'\[javac\]\s*(\d+)\s*个错误'

    # 搜索日志中的匹配项
    num_match = re.search(error_num, log_content)

    if num_match:
        error_count = int(num_match.group(1))
        print(f"错误：{error_count}个")
    else:
        print("未找到错误数量信息")

    # 预定义关键模式
    patterns = {
        'error': r'(\S+\.java:\d+):\s*错误: (.+)',
        'build_failed': r'BUILD FAILED\n(.+?):(.+)',
        'warning': r'警告: (.+?)\[javac\]',
        'java_version': r'Java\s+(\d+\.\d+)',
        'ant_task': r'Running ant \((.+?)\)',
        'dependency': r'Getting:\s+(.+?\.jar)'
    }

    # 存储结构化结果
    result = {
        'errors': [],
        'build_failed': {},
        'warnings': defaultdict(int),
        'context': {
            'java_version': None,
            'ant_tasks': [],
            'dependencies': set()
        }
    }

    # 逐行分析
    for line in log_content.split('\n'):
        if error_match := re.search(patterns['error'], line):
            filename, error_msg = error_match.groups()
            result['errors'].append({
                'file': filename,
                'error': error_msg.split('。')[0].strip(),
                'type': 'syntax' if '语法' in error_msg else 'semantic'
            })
        elif build_match := re.search(patterns['build_failed'], line):
            location, reason = build_match.groups()
            result['build_failed'] = {
                'location': location.strip(),
                'reason': reason.split('!')[0].strip()
            }
        elif warn_match := re.search(patterns['warning'], line):
            warning = warn_match.group(1).split(',')[0].strip()
            result['warnings'][warning] += 1
        elif version_match := re.search(patterns['java_version'], line):
            result['context']['java_version'] = version_match.group(1)
        elif ant_match := re.search(patterns['ant_task'], line):
            result['context']['ant_tasks'].append(ant_match.group(1))
        elif dep_match := re.search(patterns['dependency'], line):
            result['context']['dependencies'].add(dep_match.group(1))

    # 警告合并处理
    result['warnings'] = {
        f"{k} (x{v})" if v > 1 else k
        for k, v in result['warnings'].items()
    }

    # 清理空字段
    return {k: v for k, v in result.items() if v}


def format_parsed_results(parsed):
    """将解析结果格式化为字符串，并转义反斜杠"""
    output_lines = []
    if parsed.get('errors'):
        output_lines.append("=" * 40 + " 关键错误 " + "=" * 40)
        for error in parsed['errors']:
            file_path = error['file'].replace('\\', '\\\\')
            error_msg = error['error'].replace('\\', '\\\\')
            output_lines.append(f"[{error['type'].upper()}] {file_path}")
            output_lines.append(f"\t{error_msg}\n")
    if parsed.get('build_failed'):
        output_lines.append("=" * 40 + " 构建失败 " + "=" * 40)
        location = parsed['build_failed']['location'].replace('\\', '\\\\')
        reason = parsed['build_failed']['reason'].replace('\\', '\\\\')
        output_lines.append(f"位置: {location}")
        output_lines.append(f"原因: {reason}\n")
    return '\n'.join(output_lines)


def extract_failing_test_methods(log_content: str, class_name: str) -> list:
    pattern = re.compile(
        r"Failing tests: \d+\s*(.*?)(?:\n\n|\nSTDERR:|$)",
        re.DOTALL
    )
    failing_tests_section = pattern.search(log_content)
    if not failing_tests_section:
        return []
    failing_methods = []
    class_pattern = re.compile(
        rf"{re.escape(class_name)}::(\w+)",
        re.IGNORECASE
    )
    for line in failing_tests_section.group(1).split('\n'):
        line = line.strip()
        if not line.startswith('- '):
            continue
        match = class_pattern.search(line)
        if match:
            method_name = match.group(1).replace('\\', '\\\\')
            failing_methods.append(method_name)
    return failing_methods


def analyze_results(model_name="Meta-Llama-3-70B"):
    """
    分析测试结果并尝试修复编译或测试失败。

    参数:
        model_name (str): 使用的千帆模型名称，默认为 Meta-Llama-3-70B
    """
    # 初始化 Qianfan 大模型
    chat_comp = qianfan.ChatCompletion()

    # 文件路径
    file_path = "/home/zyx/Desktop/Buggy_Tester/HP/log/result_55.json"
    output_dir = "/home/zyx/Desktop/Buggy_Tester/HP/deepseek_out_55"
    max_iterations_compile = 5  # 编译错误的最大迭代次数
    max_iterations_test = 5  # 测试失败的最大迭代次数

    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"结果文件未找到: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"结果文件格式错误: {file_path}")
        return None
    except Exception as e:
        print(f"读取结果文件时出错: {e}")
        return None

    # 处理每个测试结果
    for item in data:
        try:
            sub_project_name = item.get("sub_project_name", "")
            num = item.get("num", "")
            compile_status = item.get("Compile", -1)
            test_status = item.get("Test", -1)
            log_content = item.get("log", "")
            test_case_dir = item.get("test_case_dir", "")
            name = item.get("name", "")
            project_path = item.get("project_path", "")
            ori_test_dir = item.get("ori_test_dir", "")
            java_file_path = os.path.join(test_case_dir, f"{name}.java")
            iteration = 0

            # 根据 repair_flag 设置最大迭代次数
            repair_flag = -1  # 初始化 repair_flag
            if compile_status == 0:  # compile fail
                repair_flag = 1
            elif compile_status == 1 and test_status == 0:  # test fail
                repair_flag = 2
            elif compile_status == 1 and test_status == 1:
                repair_flag = 3

            max_iterations = max_iterations_compile if repair_flag == 1 else max_iterations_test if repair_flag == 2 else max_iterations_compile

            # 持续迭代直到修复成功或达到上限
            while (compile_status != 1 or test_status != 1) and iteration < max_iterations:
                print(f"[Iteration {iteration + 1}] 处理 {name}.java")

                # 读取测试用例文件
                try:
                    with open(java_file_path, 'r', encoding='utf-8') as file:
                        testcase_content = file.read()
                        print(f"成功读取文件: {java_file_path}")
                except FileNotFoundError:
                    print(f"文件未找到: {java_file_path}")
                    item.update({
                        "Compile": 0,
                        "Test": 0,
                        "log": f"文件未找到: {java_file_path}",
                        "success": False
                    })
                    break
                except Exception as e:
                    print(f"读取文件时出错: {str(e)}")
                    item.update({
                        "Compile": 0,
                        "Test": 0,
                        "log": f"读取文件时出错: {str(e)}",
                        "success": False
                    })
                    break

                # 读取 data_122.json 文件
                try:
                    with open("/home/zyx/Desktop/Buggy_Tester/data_122.json", 'r', encoding='utf-8') as file:
                        data_summary = json.load(file)
                        print(f"成功读取文件: /home/zyx/Desktop/Buggy_Tester/data_122.json")
                except FileNotFoundError:
                    print(f"文件未找到: /home/zyx/Desktop/Buggy_Tester/data_122.json")
                    item.update({
                        "Compile": 0,
                        "Test": 0,
                        "log": f"文件未找到: /home/zyx/Desktop/Buggy_Tester/data_122.json",
                        "success": False
                    })
                    break
                except Exception as e:
                    print(f"读取文件时出错: {str(e)}")
                    item.update({
                        "Compile": 0,
                        "Test": 0,
                        "log": f"读取文件时出错: {str(e)}",
                        "success": False
                    })
                    break

                # 获取Summary（确保只取匹配的item）
                Summary = ""
                Method_body = ""
                for item_summary in data_summary:
                    project_num = item_summary.get("project_num", "")
                    if project_num == item.get("sub_project_name", "") + "_" + item.get("num", ""):
                        Summary = item_summary.get("Summary", "")
                        Method_body = item_summary.get("Method_body", "")
                        break

                # 初始化 failing_test
                failing_test = []

                # 设置repair_flag并处理错误信息
                if compile_status == 0:  # compile fail
                    repair_flag = 1
                    parsed = parse_compile_errors(log_content)
                    formatted_output = format_parsed_results(parsed)
                elif compile_status == 1 and test_status == 0:  # test fail
                    repair_flag = 2
                    failing_test = extract_failing_test_methods(log_content, name)
                elif compile_status == 1 and test_status == 1:
                    repair_flag = 3
                    formatted_output = ""  # 初始化 formatted_output
                else:
                    repair_flag = -1  # 无效状态
                    formatted_output = ""  # 初始化 formatted_output

                # 转义变量中的反斜杠
                Summary = Summary.replace('\\', '\\\\')
                formatted_output = formatted_output.replace('\\', '\\\\')
                testcase_content = testcase_content.replace('\\', '\\\\')
                Method_body = Method_body.replace('\\', '\\\\')
                if repair_flag == 2:
                    failing_test = [test.replace('\\', '\\\\') for test in failing_test]

                # 处理不同的repair_flag
                if repair_flag == 1:
                    # 第一步：让大模型理解报错信息和代码
                    understanding_prompt = (
                            "You are a Java test generation expert who is good at analyzing compilation errors and test failures.\n"
                            "Please analyze the following information and provide a detailed understanding of the issues(Whether you need to add methods to an anonymous class that might be missing.):\n"
                            "1. Whether all abstract methods are implemented correctly\n"
                            "2. The method signatures match exactly\n"
                            "[Error Details]\n" +
                            formatted_output + "\n"
                                               "[Original Test Code]\n" +
                            testcase_content
                    )
                    try:
                        print(f"[Request] 理解错误信息，模型：{model_name}")
                        response = chat_comp.do(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "You are a Java test generation expert."},
                                {"role": "user", "content": understanding_prompt},
                            ],
                            temperature=0.1,
                        )
                        understanding_content = response["body"]["result"].strip()
                        print(f"[Understanding] 对 {name}.java 的问题理解如下：\n{understanding_content}\n")
                    except Exception as e:
                        print(f"调用千帆模型理解错误信息时出错: {str(e)}")
                        item.update({
                            "Compile": 0,
                            "Test": 0,
                            "log": f"调用千帆模型理解错误信息时出错: {str(e)}",
                            "success": False
                        })
                        break

                    # 第二步：生成修复代码
                    repair_prompt = (
                        "[Critical Requirements]\n"
                        "1. Return ONLY the corrected .java file content in a code block. Note: Don't have non-code parts! No words other than code\n"
                        "2. Preserve all test methods and class structure\n"
                        "3. JDK 11 + JUnit 1.4 \n\n"
                        f"This test case has compilation errors. Please repair it based on the following analysis:\n"
                        f"[Analysis]\n{understanding_content}\n"
                        f"[Original Test Code]\n{testcase_content}"
                    )

                elif repair_flag == 2:
                    # 第一步：分析Method_body的分支结构
                    method_analysis_prompt = (
                            "You are a Java testing expert tasked with analyzing a method's control flow and semantic behavior.\n"
                            "Please analyze the following method and provide a detailed breakdown of its branch structure:\n"
                            "1. Identify all conditional branches within loops (e.g., if/else/switch statements, return/break/continue)\n"
                            "2. Identify conditions evaluated after loops (post-loop conditions)\n"
                            "3. Identify implicit branches (default paths or behaviors not explicitly defined in conditionals)\n"
                            "4. Provide a clear semantic description of the method's overall behavior\n"
                            "[Method Code]\n" +
                            Method_body + "\n"
                                          "[Environment Context]\n"
                                          "JDK 11\n"
                                          "Return the analysis in a structured format, listing each branch type separately."
                    )
                    try:
                        print(f"[Request] 分析 Method_body，模型：{model_name}")
                        response = chat_comp.do(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "You are a Java testing expert."},
                                {"role": "user", "content": method_analysis_prompt},
                            ],
                            temperature=0.1,
                        )
                        buggy_method_understanding = response["body"]["result"].strip()
                        print(f"[Method Analysis] 对 Method_body 的分支分析如下：\n{buggy_method_understanding}\n")
                    except Exception as e:
                        print(f"调用千帆模型分析 Method_body 时出错: {str(e)}")
                        item.update({
                            "Compile": 0,
                            "Test": 0,
                            "log": f"调用千帆模型分析 Method_body 时出错: {str(e)}",
                            "success": False
                        })
                        break

                    # 第二步：分析Summary并对比Method_body的分支
                    summary_analysis_prompt = (
                            "You are a Java testing expert tasked with validating a method's summary against its implementation.\n"
                            "The provided Summary describes the correct, intended behavior of the method. Your task is to:\n"
                            "1. Analyze the Summary to identify the expected branch structure (conditional branches, loop conditions, implicit branches)\n"
                            "2. Compare these expected branches with the Method_body's branch analysis to identify discrepancies\n"
                            "3. If discrepancies exist, assume the Summary is correct and note which branches in Method_body are incorrect or missing\n"
                            "[Summary]\n" +
                            Summary + "\n"
                                      "[Method_body Branch Analysis]\n" +
                            buggy_method_understanding + "\n"
                                                         "[Environment Context]\n"
                                                         "JDK 11\n"
                                                         "Return a detailed comparison, highlighting correct branches, incorrect branches, and missing branches from the Summary's perspective."
                    )
                    try:
                        print(f"[Request] 分析 Summary，模型：{model_name}")
                        response = chat_comp.do(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "You are a Java testing expert."},
                                {"role": "user", "content": summary_analysis_prompt},
                            ],
                            temperature=0.1,
                        )
                        summary_understanding = response["body"]["result"].strip()
                        print(
                            f"[Summary Analysis] 对 Summary 的分支分析及与 Method_body 的对比：\n{summary_understanding}\n")
                    except Exception as e:
                        print(f"调用千帆模型分析 Summary 时出错: {str(e)}")
                        item.update({
                            "Compile": 0,
                            "Test": 0,
                            "log": f"调用千帆模型分析 Summary 时出错: {str(e)}",
                            "success": False
                        })
                        break

                    # 第三步：分析现有测试用例并生成缺失的测试
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
                            "[Summary Branch Analysis]\n" +
                            summary_understanding + "\n"
                                                    "[Original Test Code]\n" +
                            testcase_content + "\n"
                                               "[Failing Tests]\n" +
                            "\n".join(f"- {test}" for test in failing_test) + "\n"
                                                                              "[Environment Context]\n"
                                                                              "JDK 11 + JUnit 1.4\n"
                                                                              "[Critical Requirements]\n"
                                                                              "1. Return ONLY the corrected .java file content in a code block. Note: Don't have non-code parts! No words other than code\n"
                                                                              "2. Preserve valid test methods and class structure\n"
                                                                              "3. Add new test methods only for missing or incorrect branches\n"
                    )

                elif repair_flag == 3:
                    print(f"[Success] {name}.java 已修复，无需进一步处理")
                    item.update({
                        "Compile": 1,
                        "Test": 1,
                        "log": log_content,
                        "success": True
                    })
                    break
                else:
                    print(f"[Error] 无效的 repair_flag: {repair_flag}")
                    item.update({
                        "Compile": compile_status,
                        "Test": test_status,
                        "log": f"无效的 repair_flag: {repair_flag}",
                        "success": False
                    })
                    break

                # 调用千帆模型生成修复代码
                if repair_flag in [1, 2]:
                    try:
                        print(f"[Request] 生成修复代码，模型：{model_name}")
                        response = chat_comp.do(
                            model=model_name,
                            messages=[
                                {"role": "system",
                                 "content": "I want you to play the role of a professional who writes Java test methods."},
                                {"role": "user", "content": repair_prompt},
                            ],
                            temperature=0.1,
                        )
                        generated_code = response["body"]["result"].strip()
                    except Exception as e:
                        print(f"调用千帆模型生成修复代码时出错: {str(e)}")
                        item.update({
                            "Compile": 0,
                            "Test": 0,
                            "log": f"调用千帆模型生成修复代码时出错: {str(e)}",
                            "success": False
                        })
                        break

                    filename = f"{name}.java"
                    project_nums = '{a}_{b}'.format(a=sub_project_name, b=num)
                    output_dirs = os.path.join(output_dir, project_nums)
                    output_path = os.path.join(output_dirs, filename)
                    cleaned_code = generated_code.replace("```java\n", "").strip()
                    cleaned_code = cleaned_code.replace("```", "").strip()
                    cleaned_code = re.sub(r"Here's.*?(?=\n|$)", "", cleaned_code, flags=re.IGNORECASE).strip()

                    try:
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(cleaned_code)
                        print(f"[Saved] 成功修复测试用例，已保存至：{output_path}")
                    except Exception as e:
                        print(f"保存修复代码时出错: {str(e)}")
                        item.update({
                            "Compile": 0,
                            "Test": 0,
                            "log": f"保存修复代码时出错: {str(e)}",
                            "success": False
                        })
                        break

                    # 在生成并保存修复代码后，重新测试
                    print(f"[Testing] 开始测试修复后的代码，项目路径：{project_path}")
                    try:
                        test_result = process_single_project(project_path)
                    except Exception as e:
                        print(f"测试修复代码时出错: {str(e)}")
                        item.update({
                            "Compile": 0,
                            "Test": 0,
                            "log": f"测试修复代码时出错: {str(e)}",
                            "success": False
                        })
                        break

                    if test_result:
                        print(
                            f"[Test Result] 修复后测试结果：Compile={test_result['Compile']}, Test={test_result['Test']}")
                        # 更新 item 的测试结果
                        item.update({
                            "Compile": test_result["Compile"],
                            "Test": test_result["Test"],
                            "log": test_result["log"],
                            "success": test_result["success"]
                        })
                        compile_status = test_result["Compile"]
                        test_status = test_result["Test"]
                        log_content = test_result["log"]
                    else:
                        print(f"[Test Result] 修复后测试失败，路径无效或处理出错")
                        item.update({
                            "Compile": 0,
                            "Test": 0,
                            "log": "测试修复代码失败",
                            "success": False
                        })
                        compile_status = 0
                        test_status = 0
                        log_content = "测试修复代码失败"

                    iteration += 1

                if iteration >= max_iterations and (compile_status != 1 or test_status != 1):
                    print(f"[Failed] {name}.java 达到最大迭代次数 {max_iterations}，仍未修复")
                    item.update({
                        "Compile": compile_status,
                        "Test": test_status,
                        "log": log_content,
                        "success": False
                    })

        except Exception as e:
            print(f"处理测试用例 {name}.java 时出错: {str(e)}")
            item.update({
                "Compile": 0,
                "Test": 0,
                "log": f"处理测试用例时出错: {str(e)}",
                "success": False
            })
            continue

    # 保存更新后的数据
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"保存结果文件时出错: {e}")
        return data  # 返回已处理的数据，即使保存失败

    print("处理完成！")
    return data


if __name__ == "__main__":
    # 指定千帆模型名称
    model_name = "Meta-Llama-3-70B"
    results = analyze_results(model_name)