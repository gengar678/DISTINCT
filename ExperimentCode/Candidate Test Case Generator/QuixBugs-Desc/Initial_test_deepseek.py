import json
import os
import time
from openai import OpenAI

# 初始化 OpenAI 客户端，连接 DeepSeek
client = OpenAI(api_key="Your api_key", base_url="https://api.deepseek.com")

# JSON 文件路径
json_path = "C:\\Users\\15154\\Desktop\\testcase\\quixbugs.json"

# 输出文件夹路径
output_base = "C:\\Users\\15154\\Desktop\\testcase\\quixbugs_out"

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
    all_Import_statements = under_test.get("all_Import_statements", "").strip()

    test_method = item.get("Test_method", {})

    constructors = under_test.get("constructors", "").strip()

    project_num = under_test.get("project_num", "").strip()

    print(f"正在处理{project_num}")

    if not Summary or not Class_name or not Method_name or not Method_body:
        missing_fields = []
        if not Summary: missing_fields.append("Summary")
        if not Class_name: missing_fields.append("Class_name")
        if not Method_body: missing_fields.append("Method_body")
        if not all_method_signature: missing_fields.append("all_method_signature")
        if not constructors: missing_fields.append("constructors")

        if missing_fields:
            print(f"[Warning] 第 {idx + 1} 项缺少字段: {', '.join(missing_fields)}，跳过。")
            continue

    # 构建 prompt，合并 system 和 user 内容
    prompt = f"""
Please generate the JUnit 4 test class code for the following Java methods. Requirements:

1. The methods called in the test class should be accessed by the full class name, for example, using DETECT_CYCLE.detect_cycle(...) ;
2. If the method uses a custom class (such as Node), please declare an inner class that matches the original class in the test class, or prompt that it should be imported from the original class;
3. All test methods should use the @Test(timeout = 1000) annotation, and assertions should use assertTrue or assertFalse;
4. Ensure that the test classes can be compiled and run directly in the JUnit 4 environment, and do not omit "import";
5. Do not omit any necessary class names or method qualifiers,and the class test name needs to be the same as the file name. Both are '{Class_name}_Test';

This is the method to be tested and the class it belongs to (including the class name and package name) :
Package Name: java_programs
Class Name: {Class_name}
6. The generated test cases must strictly adhere to the logic and behavior described in the "Summary" below. If the "Summary" conflicts with the "Method_body" code, prioritize the Summary's description.

## Task Description
Generate JUnit tests validating method behavior against this requirement:
**Summary**: {Summary}

## Class Structure
java
// all_Import_statements
{all_Import_statements}

{Class_declaration} {{
    // all_method_signature
    {all_method_signature}
    // Target Method
    {Method_body}
}}

## Definitions of related classes and methods

public class Node {{    public Node() public Node(String value) public Node(String value, Node successor) public Node(String value, ArrayList<Node> successors) public Node(String value, ArrayList<Node> predecessors, ArrayList<Node> successors)
public String getValue() public void setSuccessor(Node successor) public void setSuccessors(ArrayList<Node> successors) public void setPredecessors(ArrayList<Node> predecessors) public Node getSuccessor() public ArrayList<Node> getSuccessors() public ArrayList<Node> getPredecessors()
}}

public class WeightedEdge implements Comparable<WeightedEdge>{{
public WeightedEdge() public WeightedEdge(Node node1, Node node2, int weight)
public int compareTo(WeightedEdge compareNode)
}}
"""

    # 添加请求间隔以遵守 QPS 限制（假设 QPS=1）
    time.sleep(1)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(
                f"[Request] 第 {idx + 1} 项，尝试 {attempt + 1}/{max_retries}，时间：{time.strftime('%Y-%m-%d %H:%M:%S')}")

            # 调用 DeepSeek 的 ChatCompletion API
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system",
                     "content": "You are a Java testing expert who strictly follows the following rules\n"
                                "1.Always output only valid Java code which is compilable, just 'code' not ``` 'code' ``` or other natural language\n"
                                "2.Use JUnit 4 syntax\n"
                                "3.Include the necessary import statements\n"
                                "4.The generated test cases must strictly adhere to the logic and behavior described in the \"Summary\" above. If the \"Summary\" conflicts with the \"Method_body\" code, prioritize the Summary's description.\n"
                                "5.The output file must not have non-code parts, Your output must be java code and nothing else."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                stream=False
            )

            # 获取生成的代码
            generated_code = response.choices[0].message.content.strip()

            # 保存生成的代码到文件
            output_dir = os.path.join(output_base, project_num)
            os.makedirs(output_dir, exist_ok=True)
            filename = f"{Class_name}_Test.java".replace(" ", "_")
            output_path = os.path.join(output_dir, filename)

            cleaned_code = generated_code.replace("java\n", "").strip()
            final_code = f"package java_testcases.junit;\n\n{cleaned_code}"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_code)

            print(f"[Saved] 第 {idx + 1} 项生成测试用例，已保存至：{output_path}")
            break

        except Exception as e:
            error_str = str(e).lower()
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"[Retry] 第 {idx + 1} 项因错误重试 {attempt + 1}/{max_retries}，等待 {wait_time} 秒")
                time.sleep(wait_time)
            else:
                print(f"[Error] 第 {idx + 1} 项调用或保存失败：{e}")
                break
