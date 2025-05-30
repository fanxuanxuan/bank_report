import sys
import os
import re
import json
import uuid
import datetime
import base64
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import requests
import pytesseract
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['CORRECTION_DATA'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'corrections.json')

# 确保上传目录和数据目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(app.config['CORRECTION_DATA']), exist_ok=True)

# 初始化校正数据文件
if not os.path.exists(app.config['CORRECTION_DATA']):
    with open(app.config['CORRECTION_DATA'], 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    """检查文件是否为允许的扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_cloud_ocr_result(image_path):
    """
    使用云OCR服务识别图片
    这里使用模拟数据，实际应用中应替换为真实的云OCR API调用
    """
    # 模拟云OCR识别结果
    # 在实际应用中，这里应该调用真实的OCR API
    # 例如：
    # with open(image_path, 'rb') as f:
    #     image_data = base64.b64encode(f.read()).decode('utf-8')
    # response = requests.post(
    #     'https://api.ocr-service.com/recognize',
    #     json={'image': image_data},
    #     headers={'Authorization': 'Bearer YOUR_API_KEY'}
    # )
    # return response.json()
    
    # 模拟数据
    # return {
    #     "非现理财": "149.87(南) + 0.74 + 15 + 35",
    #     "现金理财": "2.63 + 130 + 105 + 100",
    #     "定期存款": "7 + 14",
    #     "低成本存款销量": "144(南) + 15.8 + 7 + 57",
    #     "开卡": "8",
    #     "手机银行": "8",
    #     "快捷支付": "7",
    #     "三类数币": "8",
    #     "企微": "8"
    # }

    """
    从图片中提取表格数据
    """
    # 使用pytesseract进行OCR识别
    print("开始OCR识别...")
    custom_config = r'--oem 3 --psm 6'
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang='chi_sim', config=custom_config)
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
    # correction = input("\n是否需要手动修正数据? (y/n): ")
    # if correction.lower() == 'y':
    #     print("手动修正后的数据:")
    #     for key in data.keys():
    #         if key in ["理财总销售", "个人存款总销量"]:
    #             continue  # 这些是计算得出的，不需要手动输入
    #         current_value = data[key]
    #         new_value = input(f"{key} [{current_value}]: ")
    #         if new_value:
    #             data[key] = new_value
    
    return data

def apply_corrections(ocr_result, image_hash):
    """
    应用历史校正数据优化OCR结果
    """
    try:
        with open(app.config['CORRECTION_DATA'], 'r', encoding='utf-8') as f:
            corrections = json.load(f)
        
        # 如果有该图片的校正记录，应用校正
        if image_hash in corrections:
            for field, value in corrections[image_hash].items():
                ocr_result[field] = value
    except Exception as e:
        print(f"应用校正数据时出错: {e}")
    
    return ocr_result

def save_correction(image_hash, field, value):
    """
    保存用户的校正数据
    """
    try:
        with open(app.config['CORRECTION_DATA'], 'r', encoding='utf-8') as f:
            corrections = json.load(f)
        
        # 如果没有该图片的记录，创建新记录
        if image_hash not in corrections:
            corrections[image_hash] = {}
        
        # 保存校正
        corrections[image_hash][field] = value
        
        with open(app.config['CORRECTION_DATA'], 'w', encoding='utf-8') as f:
            json.dump(corrections, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"保存校正数据时出错: {e}")
        return False

def calculate_image_hash(image_path):
    """
    计算图片的哈希值，用于唯一标识图片
    简单实现，实际应用中可以使用更复杂的图像哈希算法
    """
    import hashlib
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def calculate_values(data):
    """计算表格中的数据，处理带有文字和相加的情况"""
    results = {}
    
    # 处理非现理财
    if data.get("非现理财"):
        # 提取所有数字
        numbers = re.findall(r'(\d+\.?\d*)', data["非现理财"])
        if numbers:
            total = sum(float(num) for num in numbers)
            results["非现理财"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理现金理财
    if data.get("现金理财"):
        numbers = re.findall(r'(\d+\.?\d*)', data["现金理财"])
        if numbers:
            total = sum(float(num) for num in numbers)
            results["现金理财"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 计算理财总销售（非现理财 + 现金理财）
    if "非现理财" in results and "现金理财" in results:
        total = float(results["非现理财"]) + float(results["现金理财"])
        results["理财总销售"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理定期存款
    if data.get("定期存款"):
        numbers = re.findall(r'(\d+\.?\d*)', data["定期存款"])
        if numbers:
            total = sum(float(num) for num in numbers)
            results["定期存款"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理低成本存款销量
    if data.get("低成本存款销量"):
        numbers = re.findall(r'(\d+\.?\d*)', data["低成本存款销量"])
        if numbers:
            total = sum(float(num) for num in numbers)
            results["低成本存款销量"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 计算个人存款总销量（定期存款 + 低成本存款销量）
    if "定期存款" in results and "低成本存款销量" in results:
        total = float(results["定期存款"]) + float(results["低成本存款销量"])
        results["个人存款总销量"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理其他简单数值
    for key in ["开卡", "手机银行", "快捷支付", "企微"]:
        if data.get(key) and re.search(r'\d+', data[key]):
            match = re.search(r'(\d+)', data[key])
            if match:
                results[key] = match.group(1)
    
    # 处理三类数币（可能包含额外信息）
    if data.get("三类数币"):
        match = re.search(r'(\d+)', data["三类数币"])
        if match:
            results["三类数币"] = match.group(1)
    
    # 处理其他可能有值的字段
    for key in ["天天宝", "养老金账户", "白金", "黑金", "私行新增", "基金", "保险", "有效三方", "信用卡", "收单商户", "贵金属"]:
        if data.get(key) and re.search(r'\d+', data[key]):
            match = re.search(r'(\d+)', data[key])
            if match:
                results[key] = match.group(1)
    
    return results

def generate_report(results):
    """生成报告，按照模板格式填充数据"""
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
    """校验报告内容的准确性和完整性"""
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

@app.route('/')
def index():
    """首页路由"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    print("处理图片上传API")
    """处理图片上传API"""
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型，请上传图片文件（jpg, jpeg, png, gif）'}), 400
    
    # 保存文件
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    
    # 计算图片哈希值
    image_hash = calculate_image_hash(file_path)
    
    # 获取OCR识别结果
    ocr_result = get_cloud_ocr_result(file_path)
    
    # 应用历史校正数据
    ocr_result = apply_corrections(ocr_result, image_hash)
    
    # 返回提取的数据
    return jsonify({
        'data': ocr_result, 
        'file_id': unique_filename,
        'image_hash': image_hash
    })

@app.route('/api/correct', methods=['POST'])
def correct_data():
    """保存用户校正的数据"""
    # 获取请求数据
    request_data = request.json
    if not request_data or 'image_hash' not in request_data or 'field' not in request_data or 'value' not in request_data:
        return jsonify({'error': '请求数据无效'}), 400
    
    # 保存校正
    image_hash = request_data['image_hash']
    field = request_data['field']
    value = request_data['value']
    
    success = save_correction(image_hash, field, value)
    
    if success:
        return jsonify({'success': True, 'message': '校正数据已保存'})
    else:
        return jsonify({'error': '保存校正数据失败'}), 500

@app.route('/api/process', methods=['POST'])
def process_data():
    """处理数据并生成报告API"""
    # 获取请求数据
    request_data = request.json
    if not request_data or 'data' not in request_data:
        return jsonify({'error': '请求数据无效'}), 400
    
    # 计算结果
    data = request_data['data']
    results = calculate_values(data)
    
    # 生成报告
    report = generate_report(results)
    
    # 校验报告
    verification = verify_report(report)
    
    # 保存报告
    report_id = str(uuid.uuid4())
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{report_id}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    # 返回结果
    return jsonify({
        'report': report,
        'report_id': report_id,
        'verification': verification
    })

@app.route('/api/download/<report_id>', methods=['GET'])
def download_report(report_id):
    """下载报告API"""
    # 检查报告ID格式
    if not re.match(r'^[a-f0-9\-]+$', report_id):
        return jsonify({'error': '无效的报告ID'}), 400
    
    # 构建报告文件路径
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{report_id}.txt")
    
    # 检查文件是否存在
    if not os.path.exists(report_path):
        return jsonify({'error': '报告不存在'}), 404
    
    # 获取当前日期
    today = datetime.datetime.now()
    date_str = today.strftime("%Y%m%d")
    
    # 返回文件
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        f"{report_id}.txt",
        as_attachment=True,
        download_name=f"银行数据报告_{date_str}.txt"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
