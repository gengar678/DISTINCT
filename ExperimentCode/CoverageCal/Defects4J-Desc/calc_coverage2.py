import json
import re
import os

# 定义常量
input_json_path = "/home/zyx/Desktop/DISTINCT/log/coverage.json"  # JSON 文件路径
output_json_path = "/home/zyx/Desktop/DISTINCT/log/coverage_result.json"  # 输出文件路径

# 确保输出目录存在
os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

def extract_coverage(log):
    """
    从日志中提取 Line coverage 和 Condition coverage
    
    Args:
        log: 日志字符串
        
    Returns:
        tuple: (line_coverage, condition_coverage)，如果未找到或为 0%，返回 (None, None)
    """
    # 正则表达式匹配 Line coverage 和 Condition coverage
    line_pattern = r"Line coverage: (\d+\.\d+)%"
    condition_pattern = r"Condition coverage: (\d+\.\d+)%"
    
    line_coverage = None
    condition_coverage = None
    
    # 提取 Line coverage
    line_match = re.search(line_pattern, log)
    if line_match:
        line_coverage = float(line_match.group(1))
        if line_coverage == 0.0:
            line_coverage = None
    
    # 提取 Condition coverage
    condition_match = re.search(condition_pattern, log)
    if condition_match:
        condition_coverage = float(condition_match.group(1))
        if condition_coverage == 0.0:
            condition_coverage = None
    
    return line_coverage, condition_coverage

def calculate_average_coverage():
    # 读取 JSON 文件
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取 {input_json_path} 失败：{e}")
        return
    
    # 存储覆盖率数据
    line_coverages = []
    condition_coverages = []
    results = []
    
    # 遍历每个字典
    for item in data:
        project = item.get("project", "unknown")
        test_case = item.get("test_case", "unknown")
        log = item.get("coverage_log", "")
        
        if not log:
            print(f"项目 {project} 的 coverage_log 为空，跳过")
            continue
        
        # 提取覆盖率
        line_coverage, condition_coverage = extract_coverage(log)
        
        # 记录结果
        result = {
            "project": project,
            "test_case": test_case,
            "line_coverage": line_coverage,
            "condition_coverage": condition_coverage
        }
        results.append(result)
        
        # 收集所有非 None 覆盖率值
        if line_coverage is not None:
            line_coverages.append(line_coverage)
        if condition_coverage is not None:
            condition_coverages.append(condition_coverage)
        
        print(f"项目 {project}, 测试用例 {test_case}: "
              f"Line coverage = {line_coverage if line_coverage is not None else 'N/A'}%, "
              f"Condition coverage = {condition_coverage if condition_coverage is not None else 'N/A'}%")
    
    # 计算平均覆盖率
    avg_line_coverage = None
    avg_condition_coverage = None
    
    if line_coverages:
        avg_line_coverage = sum(line_coverages) / len(line_coverages)
        print(f"平均 Line coverage: {avg_line_coverage:.1f}% ({len(line_coverages)} 个有效值)")
    else:
        print("没有匹配的 Line coverage 数据")
    
    if condition_coverages:
        avg_condition_coverage = sum(condition_coverages) / len(condition_coverages)
        print(f"平均 Condition coverage : {avg_condition_coverage:.1f}% ({len(condition_coverages)} 个有效值)")
    else:
        print("没有匹配的 Condition coverage 数据")
    
    # 保存结果到 JSON 文件
    summary = {
        "results": results,
        "summary": {
            "average_line_coverage": avg_line_coverage,
            "average_condition_coverage": avg_condition_coverage,
            "line_coverage_count": len(line_coverages),
            "condition_coverage_count": len(condition_coverages),
            "all_line_coverages": line_coverages,
            "all_condition_coverages": condition_coverages
        }
    }
    
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        print(f"覆盖率统计结果已保存到 {output_json_path}")
    except Exception as e:
        print(f"保存结果失败：{e}")

def main():
    print("开始计算覆盖率...")
    calculate_average_coverage()
    print("覆盖率计算完成！")

if __name__ == "__main__":
    main()
