# Excel转Markdown工具 - Docker版本

## 快速开始

### 1. 构建Docker镜像
```bash
docker build -t excel-to-markdown .
```

### 2. 使用Docker运行转换工具

#### 方法一：直接运行
```bash
# 转换单个文件
docker run --rm -v $(pwd)/file:/app/input -v $(pwd)/output:/app/output excel-to-markdown python markdown.py input/MCIO\ 74PIN\ VT.xlsx

# 查看工作表列表
docker run --rm -v $(pwd)/file:/app/input excel-to-markdown python markdown.py input/MCIO\ 74PIN\ VT.xlsx --list-sheets
```

#### 方法二：使用docker-compose
```bash
# 启动服务
docker-compose up -d excel-to-markdown

# 进入容器执行转换
docker-compose exec excel-to-markdown python markdown.py input/MCIO\ 74PIN\ VT.xlsx

# 停止服务
docker-compose down
```

#### 方法三：启动Web服务
```bash
# 启动Web服务器
docker-compose up -d web-converter

# 在浏览器中访问 http://localhost:8000 查看文件
```

### 3. 目录结构
```
.
├── Dockerfile              # Docker构建文件
├── docker-compose.yml      # Docker Compose配置
├── requirements.txt        # Python依赖
├── markdown.py            # 主程序
├── file/                  # 输入文件目录
│   └── MCIO 74PIN VT.xlsx
└── output/               # 输出文件目录（自动创建）
    └── MCIO 74PIN VT.md
```

### 4. 常用命令

```bash
# 构建镜像
docker build -t excel-to-markdown .

# 运行转换（一次性）
docker run --rm -v $(pwd)/file:/app/input -v $(pwd)/output:/app/output excel-to-markdown python markdown.py input/your_file.xlsx

# 交互式运行
docker run -it --rm -v $(pwd)/file:/app/input -v $(pwd)/output:/app/output excel-to-markdown bash

# 查看帮助
docker run --rm excel-to-markdown python markdown.py --help
```

### 5. 环境变量
- `PYTHONUNBUFFERED=1`: 确保Python输出不被缓冲
- `LANG=C.UTF-8`: 设置UTF-8编码支持中文
- `LC_ALL=C.UTF-8`: 设置本地化支持

### 6. 卷挂载说明
- `./file:/app/input:ro`: 只读挂载输入文件目录
- `./output:/app/output`: 读写挂载输出目录
- `.:/app`: 开发时挂载整个项目目录

### 7. 故障排除

如果遇到权限问题：
```bash
# 修复输出目录权限
sudo chown -R $USER:$USER output/
```

如果遇到中文编码问题，确保文件名使用正确的转义：
```bash
docker run --rm -v $(pwd)/file:/app/input -v $(pwd)/output:/app/output excel-to-markdown python markdown.py "input/MCIO 74PIN VT.xlsx"
``` 