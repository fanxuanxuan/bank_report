# 银行数据自动处理网站

这是一个基于Flask的Web应用，用于自动处理银行数据表格图片并生成标准格式报告。

## 功能特点

- **图片上传**：支持拖放或点击上传表格图片
- **自动识别**：使用OCR技术自动识别表格中的数据
- **数据修正**：允许用户在生成报告前修正识别结果
- **自动计算**：自动处理带有文字和相加的复杂表达式
- **报告生成**：按照固定模板格式生成报告，自动填入当天日期
- **报告下载**：用户可以下载生成的报告文本文件
- **响应式设计**：支持在手机和平板上使用

## 安装说明

### 系统要求

- Python 3.6+
- Tesseract OCR 引擎

### 安装步骤

1. 克隆或下载项目代码

2. 安装Python依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 安装Tesseract OCR（如果尚未安装）
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
   
   # CentOS/RHEL
   sudo yum install tesseract tesseract-langpack-chi-sim
   
   # macOS
   brew install tesseract tesseract-lang
   
   # Windows
   # 下载安装程序：https://github.com/UB-Mannheim/tesseract/wiki
   ```

4. 创建上传目录
   ```bash
   mkdir -p uploads
   ```

## 使用方法

1. 启动应用
   ```bash
   python src/main.py
   ```

2. 在浏览器中访问 `http://localhost:5000`

3. 上传表格图片，系统会自动识别数据

4. 检查识别结果，如有错误可以手动修正

5. 点击"生成报告"按钮，系统会生成标准格式报告

6. 预览报告并下载

## 项目结构

```
bank_report_web_app/
├── src/
│   ├── main.py          # 主程序入口
│   ├── static/          # 静态文件
│   │   └── index.html   # 前端页面
│   ├── models/          # 数据模型（未使用）
│   └── routes/          # 路由模块（未使用）
├── uploads/             # 上传文件存储目录
├── requirements.txt     # 依赖列表
└── README.md            # 项目说明文档
```

## 技术栈

- **后端**：Flask
- **前端**：HTML, CSS, JavaScript, Bootstrap
- **图像处理**：Pillow, pytesseract
- **OCR引擎**：Tesseract

## 注意事项

- 图片质量会影响识别准确性，建议使用清晰的图片
- 支持的图片格式：JPG, JPEG, PNG, GIF
- 最大上传文件大小限制为16MB
- 生成的报告会自动使用当天日期
- 上传的图片和生成的报告会临时存储在服务器上

## 部署说明

### 开发环境

开发环境使用Flask内置的开发服务器：

```bash
python src/main.py
```

### 生产环境

生产环境建议使用Gunicorn或uWSGI作为WSGI服务器，并配合Nginx作为反向代理：

```bash
# 使用Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app

# 使用uWSGI
uwsgi --http 0.0.0.0:5000 --module src.main:app --processes 4
```

## 许可证

本项目仅供内部使用，未经授权不得分发或商用。
