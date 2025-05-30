# **DISTINCT: Description-Guided Non-regressive Test Case Generation**

## **1\. Introduction**

Unit testing is a cornerstone of software quality assurance. However, existing unit test generation methods predominantly focus on regression scenarios and often fall short in non - regression settings where the method under test may be faulty. To address this limitation, we propose ****DISTINCT****, a novel framework that incorporates natural - language descriptions (NLDs) of methods' intended behavior into the test case generation process.

## **2\. Datasets**

### **2.1 Defects4J - Desc and QuixBugs - Desc**

We extended the Defects4J and QuixBugs datasets to create two new datasets, ****Defects4J - Desc**** and ****QuixBugs - Desc****. Each dataset pairs every buggy method with its NLD, providing critical semantic context for test generation.

### **2.2 Dataset Structure**

The QuixBugs - Desc.json file in the DISTINCT/Datasets directory contains information about the QuixBugs - Desc dataset. It includes details such as the class name, project path, class declaration, method body, and test method information for each buggy method.


## **3\. Open - Source Code**

### **3.1 Candidate Test Case Generator**

The DISTINCT/ExperimentCode/Candidate Test Case Generator directory contains scripts for generating initial test cases.

- ****Initial_test_qianfan.py****: This script uses the Baidu Qianfan model to generate initial test cases based on the provided NLDs and buggy methods.


### **3.2 Validator & Analyzer**

The DISTINCT/ExperimentCode/Validator & Analyzer directory contains scripts for analyzing test results and attempting to repair compilation or test failures.

- ****Test_Iterator_qianfan.py****: Uses the Qianfan model to analyze test results and repair errors.
- ****Test_Iterator_deepseek.py****: Uses the DeepSeek model to analyze test results and repair errors.


### **3.3 Coverage Calculation**

The DISTINCT/ExperimentCode/CoverageCal directory contains scripts for calculating code coverage.

- ****calc_coverage.py****: Reads the result.json file, processes projects with Test == 1, calculates coverage, and saves the results.

## **4\. Environmental Requirements**

### **4.1 Prerequisites**

- Python 3.8
- Required Python libraries: openai, qianfan, chardet, json, os, re


## **5\. Research Questions (RQs)**

### **How EvoSuite and LLM-based methods perform in Non-Regression testing?**

This research question aims to evaluate the performance of EvoSuite and LLM - based methods in non - regression testing scenarios. We will measure key metrics such as compilation success rate, test - passing rate, fault detection rate, and code coverage to comprehensively assess their effectiveness.

### **How do DISTINT perform against SOTA method?**

With the assistance of the comment, we evaluate whether baseline methods such as ChatTester, ChatUniTest, and Basic Prompt exhibit improvements in defect detection, coverage, and other relevant aspects, and compare the results with our approach. To ensure experimental fairness, we modified the source code of these baseline methods by incorporating the comment into their original frameworks.

### **RQ3: Which components of DISTINCT contribute most to branch coverage and defect detection?**

Ablation studies are conducted to understand the individual and combined contributions of the Generator, Validator, and Analyzer components to DISTINCT's performance in terms of compilation success, execution correctness, and defect detection.

### **RQ4: Can DISTINCT maintain high coverage and defect detection across different LLMs?**

To assess the generalization capability of our proposed approach across different LLMs, we replace the original commercial model, DeepSeek - V3, with three representative alternatives: LLaMA3 - 70B, a high - capacity open - source model; LLaMA3 - 8B, a medium - scale model; and CodeLLaMA - 7B, a model specifically optimized for code - related tasks. By conducting comparative experiments under these different model configurations, we systematically investigate the stability and adaptability of our approach in cross - model transfer scenarios.

### **RQ5: How do hyperparameter settings affect the performance of DISTINCT in defect detection?**

To evaluate the impact of different hyperparameter settings in DISTINCT on the experimental results, we adjust the maximum number of iterations for both the analyzer and validator components. In addition, we strictly control the number of generated test cases. These configurations allow us to explore how such variations influence the defect detection effectiveness of our approach.


## **6\. Getting Started**

### **6.1 Clone the repository**

```bash
git clone &lt;repository_url&gt;cd DISTINCT
```

### **6.2 Data Preparation**

Ensure that the Defects4J - Desc and QuixBugs - Desc datasets are available and the file paths in the scripts are correctly configured.

### **6.3 Running Experiments**

#### **6.3.1 Generate Initial Test Cases**

```bash
python DISTINCT/ExperimentCode/Candidate Test Case Generator/Defects4J - Desc/Initial_test_qianfan.py
```
#### **6.3.2 Analyze and Repair Test Results**

```bash
python DISTINCT/ExperimentCode/Validator & Analyzer/Defects4J - Desc/Test_Iterator_deepseek.py
```
#### **6.3.3 Calculate Coverage**

```bash
python DISTINCT/ExperimentCode/CoverageCal/Defects4J - Desc/calc_coverage.py
```
## **7\. Configuration**

- ****API Keys****: Replace "Your api_key" in relevant files with your actual API keys.
- ****File Paths****: Update the file paths in the scripts according to your local environment, such as json_path, output_base, etc.

## **8\. Contribution**

Contributions to this project are welcome. Please follow these steps:

1.  Lead the first in-depth study of unit-test generation in the non-regression setting, where the focal method may be faulty.
2.  Construct two enriched datasets—Defects4J-Desc and QuixBugs-Desc—annotated with comments and paired buggy/repaired methods.
3.  Propose Distinct, a novel framework that integrates LLM-based generation with semantic refinement via branch-consistency analysis.
4.  Extensive experimental results demonstrate that DISTINCT substantially outperforms state-of-the-art tools in both defect detection and test coverage.
