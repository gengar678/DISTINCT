import json
import os
import re
import qianfan
import time

# 设置Qianfan API密钥
os.environ["QIANFAN_ACCESS_KEY"] = "Your QIANFAN_ACCESS_KEY"
os.environ["QIANFAN_SECRET_KEY"] = "Your QIANFAN_SECRET_KEY"

# 初始化Qianfan大模型
chat_comp = qianfan.ChatCompletion()

# JSON 文件路径
json_path = "The path of datasets"

# 输出文件夹路径
output_base = "The path of output"

Your_Model = "Meta-Llama-3-70B"

# 读取 JSON 文件
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 遍历每个大字典
for idx, item in enumerate(data):
    under_test = item.get("Under_test_method", {})
    project_path = under_test.get("project_path", "").strip()
    Class_name = under_test.get("Class_name", "").strip()
    Method_name = under_test.get("Method_name", "").strip()
    Summary = under_test.get("Summary", "").strip()
    Method_body = under_test.get("Method_body", "").strip()
    all_method_signature = under_test.get("all_method_signature", "").strip()
    Class_declaration = under_test.get("Class_declaration", "").strip()
    all_Import_statements = under_test.get("all_Import_statements", [])
    
    test_method = item.get("Test_method", {})
    
    all_field_declaration = under_test.get("all_field_declaration", [])
    if isinstance(all_field_declaration, list):
        all_field_declaration = "\n    ".join(all_field_declaration)
    else:
        all_field_declaration = ""

    constructors = under_test.get("constructors", "").strip()
    
    if isinstance(all_Import_statements, list):
        all_Import_statements = "\n    ".join(all_Import_statements)
    else:
        all_Import_statements = ""
    
    project_num = under_test.get("project_num", "").strip()

    match = re.search(r'/(org|com)(/[\w\d_]+)+', project_path)
    if not match:
        print(f"[Warning] 第 {idx + 1} 项 project_path 无效，跳过。")
        continue

    full_match = match.group()
    package_path = os.path.dirname(full_match)
    package_path = package_path.strip("/").replace("/", ".")

    print(f"正在处理{project_num}")

    if not Summary or not Class_name or not Method_name or not Method_body:
        missing_fields = []
        if not Summary: missing_fields.append("Summary")
        if not Class_name: missing_fields.append("Class_name")
        if not Method_body: missing_fields.append("Method_body")
        if not all_method_signature: missing_fields.append("all_method_signature")
        if not all_field_declaration: missing_fields.append("all_field_declaration")
        if not constructors: missing_fields.append("constructors")

        if missing_fields:
            print(f"[Warning] 第 {idx + 1} 项缺少字段: {', '.join(missing_fields)}，跳过。")
            continue

    # 构建 prompt，合并 system 和 user 内容
    prompt = f"""
You are a Java testing expert who strictly follows the following rules:
1. Ensure that the output can only be whole and compilable java code(No natural language description (e.g.Here is the generated JUnit test class for the `computeValue` method in the `CoreOperationRelationalExpression` class:))
2. Use JUnit 4 syntax
3. Include the necessary import statements
4. The generated test cases must strictly adhere to the logic and behavior described in the "Summary" below. If the "Summary" conflicts with the "Method_body" code, prioritize the Summary's description.

## Task Description
Generate JUnit tests validating method behavior against this requirement:
**Summary**: {Summary}

## Class Structure
```java
// Package: {package_path}
// Import_statements: {all_Import_statements}
{Class_declaration} {{

    // Target Method
    {Method_body}
}}
"""

    # 添加请求间隔以遵守 QPS 限制（假设 QPS=1）
    time.sleep(1)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"[Request] 第 {idx + 1} 项，尝试 {attempt + 1}/{max_retries}，时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")
            response = chat_comp.do(
                model=Your_Model,
                messages=[
                    {"role": "user",
                     "content": prompt},
                ],
                temperature=0.1,
            )

            # 尝试获取速率限制相关头信息
            try:
                remaining_requests = response.get("X-Ratelimit-Remaining-Requests", "未知")
                remaining_tokens = response.get("X-Ratelimit-Remaining-Tokens", "未知")
                print(f"[Rate Limit Info] 剩余请求: {remaining_requests}, 剩余 Token: {remaining_tokens}")
            except:
                print("[Rate Limit Info] 无法获取速率限制头信息")

            generated_code = response["body"]["result"].strip()

            output_dir = os.path.join(output_base, project_num)
            os.makedirs(output_dir, exist_ok=True)
            filename = f"{Class_name}Test.java".replace(" ", "_")
            output_path = os.path.join(output_dir, filename)

            cleaned_code = generated_code.replace("```java\n", f"package {package_path};\n").strip()
            cleaned_code = cleaned_code.replace("```", "").strip()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned_code)

            print(f"[Saved] 第 {idx + 1} 项生成测试用例，已保存至：{output_path}")
            break

        except Exception as e:
            error_str = str(e).lower()
            if attempt < max_retries - 1 and any(code in error_str for code in ["336501", "336502", "code: 4"]):
                wait_time = 2 ** attempt
                print(f"[Retry] 第 {idx + 1} 项因速率限制失败，重试 {attempt + 1}/{max_retries}，等待 {wait_time} 秒")
                time.sleep(wait_time)
            else:
                print(f"[Error] 第 {idx + 1} 项调用或保存失败：{e}")
                break
