import sys
import os
import re
import datetime
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """检查文件是否为允许的扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_data_from_image(image_path):
    """从图片中提取表格数据"""
    try:
        # 使用pytesseract进行OCR识别
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(Image.open(image_path), lang='chi_sim+eng', config=custom_config)
        
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
        
        return data, None
    except Exception as e:
        return None, str(e)

def calculate_values(data):
    """计算表格中的数据，处理带有文字和相加的情况"""
    results = {}
    
    # 处理非现理财
    if data["非现理财"]:
        # 提取所有数字
        numbers = re.findall(r'(\d+\.?\d*)', data["非现理财"])
        if numbers:
            total = sum(float(num) for num in numbers)
            results["非现理财"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理现金理财
    if data["现金理财"]:
        numbers = re.findall(r'(\d+\.?\d*)', data["现金理财"])
        if numbers:
            total = sum(float(num) for num in numbers)
            results["现金理财"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 计算理财总销售（非现理财 + 现金理财）
    if "非现理财" in results and "现金理财" in results:
        total = float(results["非现理财"]) + float(results["现金理财"])
        results["理财总销售"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理定期存款
    if data["定期存款"]:
        numbers = re.findall(r'(\d+\.?\d*)', data["定期存款"])
        if numbers:
            total = sum(float(num) for num in numbers)
            results["定期存款"] = f"{total:.2f}".rstrip('0').rstrip('.') if '.' in f"{total:.2f}" else f"{total:.0f}"
    
    # 处理低成本存款销量
    if data["低成本存款销量"]:
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
        if data[key] and re.search(r'\d+', data[key]):
            match = re.search(r'(\d+)', data[key])
            if match:
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
    
    # 提取数据
    data, error = extract_data_from_image(file_path)
    if error:
        return jsonify({'error': f'图片识别失败: {error}'}), 500
    
    # 返回提取的数据
    return jsonify({'data': data, 'file_id': unique_filename})

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
