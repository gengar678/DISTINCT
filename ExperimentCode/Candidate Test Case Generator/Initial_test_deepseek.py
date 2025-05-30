import json
import os
import re
from openai import OpenAI

# 初始化 OpenAI 客户端
client = OpenAI(api_key="Your api_key", base_url="https://api.deepseek.com")

# JSON 文件路径
json_path = "The path of datasets"

# 输出文件夹路径
output_base = "The path of output"

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

    full_match = match.group()
    # 去掉文件名（即最后一个目录后面的 .java 文件）
    package_path = os.path.dirname(full_match)
    # 替换 / 为 .
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

    # 构建 prompt
    prompt = f"""
    ## Task Description
    Generate JUnit tests validating method behavior against this requirement:
    **Requirement**: {Summary}

    ## Class Structure
    ```java
    // Package: {package_path}
    // Import_statements: {all_Import_statements}
    {Class_declaration} {{
        // Fields
        {all_field_declaration or "// No fields"}

        // Constructors
        {constructors or "// No explicit constructors"}

        // Target Method
        {Method_body}
    }}
    """

    try:
        # 调用大模型
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system",
                 "content": "You are a Java testing expert who strictly follows the following rules\n"
                            "1.Always output only valid Java code\n"
                            "2.Use JUnit 4 syntax \n"
                            "3.Include the necessary import statements \n"
                            "4.The generated test cases must strictly adhere to the logic and behavior described in the \"Summary\" above. If the \"Summary\" conflicts with the \"Method_body\" code, prioritize the Summary\'s description.\n"
                            "5.The output file must not have non-code parts,Your output must be java code and nothing else."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            stream=False
        )

        generated_code = response.choices[0].message.content.strip()

        # 构造保存路径
        output_dir = os.path.join(output_base, project_num)
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{Class_name}Test.java".replace(" ", "_")
        output_path = os.path.join(output_dir, filename)

        cleaned_code = generated_code.replace("```java\n", f"package {package_path};\n").strip()
        cleaned_code = cleaned_code.replace("```", "").strip()
        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)

        print(f"[Saved] 第 {idx + 1} 项生成测试用例，已保存至：{output_path}")

    except Exception as e:
        print(f"[Error] 第 {idx + 1} 项调用或保存失败：{e}")

