# 银行数据自动处理系统

这是一个基于Flask的Web应用，用于自动处理银行数据表格图片并生成标准格式报告，具有OCR识别和数据记忆功能。

## 功能特点

- **图片上传**：支持拖放或点击上传表格图片
- **OCR识别**：使用云OCR技术自动识别表格中的数据
- **数据记忆**：记住用户的手动校正，下次识别相同图片时自动应用
- **数据修正**：允许用户在生成报告前修正识别结果
- **自动计算**：自动处理带有文字和相加的复杂表达式
- **报告生成**：按照固定模板格式生成报告，自动填入当天日期
- **报告下载**：用户可以下载生成的报告文本文件
- **响应式设计**：支持在手机和平板上使用

## 安装说明

### 系统要求

- Python 3.6+
- Flask 框架
- 云OCR服务（或本地OCR引擎）

### 安装步骤

1. 克隆或下载项目代码

2. 安装Python依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 创建必要的目录
   ```bash
   mkdir -p uploads data
   ```

4. 配置OCR服务
   - 如使用云OCR服务，请在`src/main.py`中更新API密钥和端点
   - 如使用本地OCR，请安装相应的OCR引擎和依赖

## 使用方法

1. 启动应用
   ```bash
   python src/main.py
   ```

2. 在浏览器中访问 `http://localhost:5000`

3. 上传表格图片，系统会自动识别数据

4. 检查识别结果，如有错误可以手动修正（系统会记住您的修正）

5. 点击"生成报告"按钮，系统会生成标准格式报告

6. 预览报告并下载

## API文档

### 1. 上传图片

- **URL**: `/api/upload`
- **方法**: `POST`
- **参数**: 
  - `file`: 图片文件（multipart/form-data）
- **响应**:
  ```json
  {
    "data": {
      "非现理财": "149.87(南) + 0.74 + 15 + 35",
      "现金理财": "2.63 + 130 + 105 + 100",
      ...
    },
    "file_id": "unique_filename",
    "image_hash": "image_hash_value"
  }
  ```

### 2. 保存校正

- **URL**: `/api/correct`
- **方法**: `POST`
- **参数**: 
  ```json
  {
    "image_hash": "image_hash_value",
    "field": "字段名称",
    "value": "校正后的值"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "校正数据已保存"
  }
  ```

### 3. 处理数据生成报告

- **URL**: `/api/process`
- **方法**: `POST`
- **参数**: 
  ```json
  {
    "data": {
      "非现理财": "149.87(南) + 0.74 + 15 + 35",
      "现金理财": "2.63 + 130 + 105 + 100",
      ...
    }
  }
  ```
- **响应**:
  ```json
  {
    "report": "报告内容...",
    "report_id": "report_id",
    "verification": {
      "is_valid": true,
      "missing_lines": [],
      "errors": []
    }
  }
  ```

### 4. 下载报告

- **URL**: `/api/download/{report_id}`
- **方法**: `GET`
- **响应**: 文本文件下载

## 项目结构

```
bank_report_ocr_backend/
├── src/
│   ├── main.py          # 主程序入口
│   ├── static/          # 静态文件
│   │   └── index.html   # 前端页面
│   ├── models/          # 数据模型（未使用）
│   └── routes/          # 路由模块（未使用）
├── uploads/             # 上传文件存储目录
├── data/                # 数据存储目录
│   └── corrections.json # 校正数据记忆文件
├── requirements.txt     # 依赖列表
└── README.md            # 项目说明文档
```

## 技术栈

- **后端**：Flask, Python
- **前端**：HTML, CSS, JavaScript, Bootstrap
- **OCR服务**：云OCR API（可替换为本地OCR）
- **数据存储**：JSON文件（可扩展为数据库）

## 数据记忆机制

系统使用图片哈希值作为唯一标识，记住用户对每个图片的校正：

1. 当用户上传图片时，系统计算图片的哈希值
2. 系统检查是否有该哈希值的历史校正数据
3. 如果有，自动应用这些校正到识别结果中
4. 当用户修改识别结果时，系统保存这些修改
5. 下次上传相同图片时，系统会自动应用这些校正

这种机制使系统能够"学习"用户的校正，不断提高识别准确率。

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
