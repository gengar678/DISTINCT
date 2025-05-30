import xml.etree.ElementTree as ET

def parse_coverage(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    line_coverages = []
    branch_coverages = []
    results = []

    for sourcefile in root.findall('.//sourcefile'):
        name = sourcefile.attrib['name']
        line_missed = line_covered = branch_missed = branch_covered = None

        for counter in sourcefile.findall('counter'):
            ctype = counter.attrib['type']
            missed = int(counter.attrib['missed'])
            covered = int(counter.attrib['covered'])
            if ctype == 'LINE':
                line_missed = missed
                line_covered = covered
            elif ctype == 'BRANCH':
                branch_missed = missed
                branch_covered = covered

        # 行覆盖率
        if line_covered is not None and line_covered != 0:
            total = line_missed + line_covered
            line_cov = line_covered / total if total > 0 else 0
            line_coverages.append(line_cov)
            line_cov_str = f"{line_cov * 100:.2f}%"
        else:
            results.append(f"name:{name},编译失败")
            continue

        # 分支覆盖率
        if branch_covered is not None and branch_covered != 0:
            total = branch_missed + branch_covered
            branch_cov = branch_covered / total if total > 0 else 0
            branch_coverages.append(branch_cov)
            branch_cov_str = f"{branch_cov * 100:.2f}%"
        else:
            branch_cov_str = "编译失败"

        results.append(f"name:{name},line coverage:{line_cov_str},branch coverage:{branch_cov_str}")

    # 计算平均覆盖率
    if line_coverages:
        avg_line = sum(line_coverages) / len(line_coverages) * 100
    else:
        avg_line = 0
    if branch_coverages:
        avg_branch = sum(branch_coverages) / len(branch_coverages) * 100
    else:
        avg_branch = 0

    results.append(f"所有文件平均行覆盖率: {avg_line:.2f}%")
    results.append(f"所有文件平均分支覆盖率: {avg_branch:.2f}%")

    return "\n".join(results)

if __name__ == "__main__":
    print(parse_coverage("宇翔哥/no_method.xml"))