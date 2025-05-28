#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import datetime
import os
import argparse
from PIL import Image
import pytesseract

def extract_data_from_image(image_path):
    """
    从图片中提取表格数据
    """
    # 使用pytesseract进行OCR识别
    custom_config = r'--oem 3 --psm 6'
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang='chi_sim+eng', config=custom_config)
    except Exception as e:
        print(f"OCR识别失败: {e}")
        return None
    
    # 初始化数据字典
    data = {
        "理财总销售": "",
        "非现理财": "",
        "现金理财": "",
        "合格投资者类": "",
        "结构性存款": "",
        "定期存款": "",
        "低成本存款销量": "",
        "个人存款总销量": "",
        "开卡": "",
        "手机银行": "",
        "快捷支付": "",
        "三类数币": "",
        "天天宝": "",
        "养老金账户": "",
        "白金": "",
        "黑金": "",
        "私行新增": "",
        "基金": "",
        "保险": "",
        "信用卡": "",
        "企微": ""
    }
    
    # 从图片中提取数据
    lines = text.split('\n')
    current_key = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 尝试匹配键值对
        for key in data.keys():
            if key in line:
                parts = line.split(key)
                if len(parts) > 1:
                    data[key] = parts[1].strip()
                    current_key = key
                    break
                else:
                    current_key = key
        
        # 如果当前行不包含键但有值，且我们有一个当前键，则将值添加到当前键
        if current_key and line and current_key not in line:
            if not data[current_key]:
                data[current_key] = line
            else:
                data[current_key] += " " + line
    
    # 如果OCR识别不准确，可以手动检查并修正数据
    print("提取的原始数据:")
    for key, value in data.items():
        if value:
            print(f"{key}: {value}")
    
    # 询问用户是否需要手动修正数据
    correction = input("\n是否需要手动修正数据? (y/n): ")
    if correction.lower() == 'y':
        for key in data.keys():
            if key in ["理财总销售", "个人存款总销量"]:
                continue  # 这些是计算得出的，不需要手动输入
            current_value = data[key]
            new_value = input(f"{key} [{current_value}]: ")
            if new_value:
                data[key] = new_value
    
    return data

def calculate_values(data):
    """
    计算表格中的数据，处理带有文字和相加的情况
    """
    results = {}
    
    # 处理非现理财
    if data["非现理财"]:
        # 提取所有数字
        numbers = re.findall(r'(\d+\.?\d*)', data["非现理财"])
        total = sum(float(num) for num in numbers)
        results["非现理财"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理现金理财
    if data["现金理财"]:
        numbers = re.findall(r'(\d+\.?\d*)', data["现金理财"])
        total = sum(float(num) for num in numbers)
        results["现金理财"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 计算理财总销售（非现理财 + 现金理财）
    if "非现理财" in results and "现金理财" in results:
        total = float(results["非现理财"]) + float(results["现金理财"])
        results["理财总销售"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理定期存款
    if data["定期存款"]:
        numbers = re.findall(r'(\d+\.?\d*)', data["定期存款"])
        total = sum(float(num) for num in numbers)
        results["定期存款"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理低成本存款销量
    if data["低成本存款销量"]:
        numbers = re.findall(r'(\d+\.?\d*)', data["低成本存款销量"])
        total = sum(float(num) for num in numbers)
        results["低成本存款销量"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 计算个人存款总销量（定期存款 + 低成本存款销量）
    if "定期存款" in results and "低成本存款销量" in results:
        total = float(results["定期存款"]) + float(results["低成本存款销量"])
        results["个人存款总销量"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理其他简单数值
    for key in ["开卡", "手机银行", "快捷支付", "企微"]:
        if data[key] and re.search(r'\d+', data[key]):
            match = re.search(r'(\d+)', data[key])
            results[key] = match.group(1)
    
    # 处理三类数币（可能包含额外信息）
    if data["三类数币"]:
        match = re.search(r'(\d+)', data["三类数币"])
        if match:
            results["三类数币"] = match.group(1)
    
    # 处理其他可能有值的字段
    for key in ["天天宝", "养老金账户", "白金", "黑金", "私行新增", "基金", "保险", "有效三方", "信用卡", "收单商户", "贵金属"]:
        if data[key] and re.search(r'\d+', data[key]):
            match = re.search(r'(\d+)', data[key])
            results[key] = match.group(1)
    
    return results

def generate_report(results):
    """
    生成报告，按照模板格式填充数据
    """
    # 获取当前日期
    today = datetime.datetime.now()
    month = today.month
    day = today.day
    
    # 创建报告模板
    report = f"""中心支行
{month}月{day}日
理财总销量:{results.get("理财总销售", "")} w
非现理财:{results.get("非现理财", "")} w
现金理财:{results.get("现金理财", "")} w
私行战略销售类:{results.get("私行战略销售类", "")}
财富战略销售:{results.get("财富战略销售", "")}
结构性存款:{results.get("结构性存款", "")}
定期存款:{results.get("定期存款", "")} w
低成本存款销量:{results.get("低成本存款销量", "")} w
个人存款总销量:{results.get("个人存款总销量", "")} w
开卡:{results.get("开卡", "")}
快捷支付:{results.get("快捷支付", "")}
手机银行:{results.get("手机银行", "")}
三类数币:{results.get("三类数币", "")}
天天宝:{results.get("天天宝", "")}
养老账户:{results.get("养老金账户", "")}
白金:{results.get("白金", "")}
黑金:{results.get("黑金", "")}
私行新增:{results.get("私行新增", "")}
基金:{results.get("基金", "")}
保险:{results.get("保险", "")}
有效三方:{results.get("有效三方", "")}
信用卡:{results.get("信用卡", "")}
收单商户:{results.get("收单商户", "")}
企微:{results.get("企微", "")}
贵金属:{results.get("贵金属", "")}"""
    
    return report

def verify_report(report):
    """
    校验报告内容的准确性和完整性
    """
    # 检查报告是否包含所有必要的行
    required_lines = [
        "中心支行",
        "月",
        "日",
        "理财总销量:",
        "非现理财:",
        "现金理财:",
        "私行战略销售类:",
        "财富战略销售:",
        "结构性存款:",
        "定期存款:",
        "低成本存款销量:",
        "个人存款总销量:",
        "开卡:",
        "快捷支付:",
        "手机银行:",
        "三类数币:",
        "天天宝:",
        "养老账户:",
        "白金:",
        "黑金:",
        "私行新增:",
        "基金:",
        "保险:",
        "有效三方:",
        "信用卡:",
        "收单商户:",
        "企微:",
        "贵金属:"
    ]
    
    report_lines = report.split('\n')
    missing_lines = []
    
    for required in required_lines:
        found = False
        for line in report_lines:
            if required in line:
                found = True
                break
        if not found:
            missing_lines.append(required)
    
    # 检查数值的合理性
    errors = []
    
    # 提取数值
    total_sales = None
    non_cash_sales = None
    cash_sales = None
    term_deposit = None
    low_cost_deposit = None
    personal_deposit = None
    
    for line in report_lines:
        if "理财总销量:" in line:
            match = re.search(r'理财总销量:(\d+\.?\d*)', line)
            if match:
                total_sales = float(match.group(1))
        elif "非现理财:" in line:
            match = re.search(r'非现理财:(\d+\.?\d*)', line)
            if match:
                non_cash_sales = float(match.group(1))
        elif "现金理财:" in line:
            match = re.search(r'现金理财:(\d+\.?\d*)', line)
            if match:
                cash_sales = float(match.group(1))
        elif "定期存款:" in line:
            match = re.search(r'定期存款:(\d+\.?\d*)', line)
            if match:
                term_deposit = float(match.group(1))
        elif "低成本存款销量:" in line:
            match = re.search(r'低成本存款销量:(\d+\.?\d*)', line)
            if match:
                low_cost_deposit = float(match.group(1))
        elif "个人存款总销量:" in line:
            match = re.search(r'个人存款总销量:(\d+\.?\d*)', line)
            if match:
                personal_deposit = float(match.group(1))
    
    # 验证理财总销量
    if total_sales is not None and non_cash_sales is not None and cash_sales is not None:
        expected_total = non_cash_sales + cash_sales
        if abs(total_sales - expected_total) > 0.01:  # 允许0.01的误差
            errors.append(f"理财总销量计算错误: {total_sales} != {non_cash_sales} + {cash_sales}")
    
    # 验证个人存款总销量
    if personal_deposit is not None and term_deposit is not None and low_cost_deposit is not None:
        expected_personal = term_deposit + low_cost_deposit
        if abs(personal_deposit - expected_personal) > 0.01:  # 允许0.01的误差
            errors.append(f"个人存款总销量计算错误: {personal_deposit} != {term_deposit} + {low_cost_deposit}")
    
    return {
        "missing_lines": missing_lines,
        "errors": errors,
        "is_valid": len(missing_lines) == 0 and len(errors) == 0
    }

def main():
    """
    主函数，处理命令行参数并执行程序
    """
    parser = argparse.ArgumentParser(description='银行数据自动处理工具')
    parser.add_argument('--image', type=str, help='输入图片路径')
    parser.add_argument('--output', type=str, default='report.txt', help='输出报告路径')
    args = parser.parse_args()
    
    # 如果没有提供图片路径，提示用户输入
    image_path = args.image
    if not image_path:
        image_path = input("请输入图片路径: ")
    
    # 检查图片是否存在
    if not os.path.exists(image_path):
        print(f"错误: 图片 {image_path} 不存在")
        return
    
    # 提取数据
    data = extract_data_from_image(image_path)
    if not data:
        print("数据提取失败")
        return
    
    # 计算结果
    results = calculate_values(data)
    
    # 生成报告
    report = generate_report(results)
    
    # 校验报告
    verification = verify_report(report)
    
    # 输出报告
    print("\n生成的报告:")
    print(report)
    
    # 输出验证结果
    print("\n验证结果:", "通过" if verification["is_valid"] else "失败")
    if not verification["is_valid"]:
        if verification["missing_lines"]:
            print("缺少行:", ", ".join(verification["missing_lines"]))
        if verification["errors"]:
            print("计算错误:")
            for error in verification["errors"]:
                print("  -", error)
    
    # 保存报告
    output_path = args.output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n报告已保存到: {output_path}")

if __name__ == "__main__":
    main()
