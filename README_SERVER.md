# GIBH-AGENT-V2 测试服务器使用说明

## 快速开始

### 1. 安装依赖

```bash
cd /home/ubuntu/GIBH-AGENT-V2
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
export SILICONFLOW_API_KEY="your_api_key_here"
```

### 3. 启动服务器

```bash
# 方式1: 使用启动脚本
./run_server.sh

# 方式2: 直接运行
python server.py

# 方式3: 使用 uvicorn
uvicorn server:app --host 0.0.0.0 --port 8018 --reload
```

### 4. 访问前端

打开浏览器访问: `http://localhost:8018`

## 功能说明

### 前端界面

- **左侧面板**: 对话界面
  - 可以输入消息或上传文件
  - 支持 `.h5ad`, `.mtx`, `.tsv`, `.csv` 等格式
  - 实时显示对话内容

- **右侧面板**: 实时日志监控
  - 自动连接日志流
  - 实时显示后台日志
  - 支持清空日志和自动滚动

### API 接口

1. **GET /** - 前端页面
2. **POST /api/upload** - 文件上传
3. **POST /api/chat** - 聊天接口
4. **POST /api/execute** - 执行工作流
5. **GET /api/logs/stream** - 实时日志流（SSE）
6. **GET /api/logs** - 获取历史日志

### 日志监控

服务器会实时输出日志到：
- 终端（标准输出）
- 日志文件：`gibh_agent.log`
- Web 前端（实时流式传输）

日志级别：
- INFO: 绿色
- WARNING: 橙色
- ERROR: 红色
- DEBUG: 蓝色

## 测试流程

1. 启动服务器后，打开浏览器访问 `http://localhost:8018`
2. 在右侧日志面板确认连接状态为"已连接"
3. 上传一个 `.h5ad` 文件或输入消息
4. 点击"发送"按钮
5. 观察：
   - 左侧对话面板显示处理结果
   - 右侧日志面板实时显示后台日志
   - 终端也会同步输出日志

## 故障排查

### 问题1: 智能体初始化失败

**现象**: 日志显示 "❌ GIBH-AGENT 初始化失败"

**解决**:
- 检查 `config/settings.yaml` 配置
- 确认 `SILICONFLOW_API_KEY` 环境变量已设置
- 查看详细错误日志

### 问题2: 日志流连接失败

**现象**: 前端显示"连接断开"

**解决**:
- 检查服务器是否正常运行
- 检查防火墙设置
- 查看浏览器控制台错误信息

### 问题3: 文件上传失败

**现象**: 上传文件后提示错误

**解决**:
- 检查 `uploads/` 目录权限
- 确认文件大小不超过限制
- 查看服务器日志

## 目录结构

```
GIBH-AGENT-V2/
├── server.py              # 测试服务器
├── requirements.txt       # Python 依赖
├── run_server.sh         # 启动脚本
├── uploads/              # 上传文件目录
├── results/              # 分析结果目录
├── gibh_agent.log        # 日志文件
└── gibh_agent/           # 智能体代码
```

## 注意事项

1. **API Key**: 必须设置 `SILICONFLOW_API_KEY` 环境变量
2. **端口**: 默认端口 8018，可通过环境变量 `PORT` 修改
3. **文件大小**: 默认支持大文件上传，可根据需要调整
4. **日志文件**: 日志会同时写入 `gibh_agent.log` 文件

## 开发模式

服务器支持热重载，修改代码后会自动重启：

```bash
uvicorn server:app --host 0.0.0.0 --port 8018 --reload
```

