"""
GIBH-AGENT-V2 测试服务器
提供简单的 Web 接口用于测试功能，支持实时日志监控
"""
import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime
from collections import deque

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from gibh_agent import create_agent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gibh_agent.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="GIBH-AGENT-V2 Test Server")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# 添加静态文件服务（用于访问结果图片）
from fastapi.staticfiles import StaticFiles
app.mount("/results", StaticFiles(directory="results"), name="results")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 初始化智能体
agent = None
try:
    # 尝试从当前目录加载配置
    config_path = Path(__file__).parent / "gibh_agent" / "config" / "settings.yaml"
    logger.info(f"🔍 查找配置文件: {config_path}")
    logger.info(f"📂 配置文件存在: {config_path.exists()}")
    
    if not config_path.exists():
        # 如果不存在，尝试其他路径
        alt_path = Path(__file__).parent / "config" / "settings.yaml"
        logger.info(f"🔍 尝试备用路径: {alt_path}")
        if alt_path.exists():
            config_path = alt_path
        else:
            config_path = "gibh_agent/config/settings.yaml"
            logger.info(f"🔍 使用默认路径: {config_path}")
    
    logger.info(f"📄 使用配置文件: {config_path}")
    
    # 设置 scanpy 工具的默认输出目录（使用相对路径）
    import os
    scanpy_output_dir = os.path.join(os.getcwd(), "results")
    logger.info(f"📁 Scanpy 输出目录: {scanpy_output_dir}")
    
    # 创建智能体
    agent = create_agent(str(config_path))
    
    # 更新 scanpy 工具的输出目录
    if agent and hasattr(agent, 'agents') and 'rna_agent' in agent.agents:
        rna_agent = agent.agents['rna_agent']
        if hasattr(rna_agent, 'scanpy_tool'):
            rna_agent.scanpy_tool.output_dir = scanpy_output_dir
            os.makedirs(scanpy_output_dir, exist_ok=True)
            logger.info(f"✅ 已设置 Scanpy 输出目录: {scanpy_output_dir}")
    
    logger.info("✅ GIBH-AGENT 初始化成功")
except Exception as e:
    import traceback
    error_msg = f"❌ GIBH-AGENT 初始化失败: {e}"
    logger.error(error_msg, exc_info=True)
    logger.error(f"详细错误:\n{traceback.format_exc()}")
    agent = None


# 请求模型
class ChatRequest(BaseModel):
    message: str = ""
    history: List[dict] = []
    uploaded_files: List[dict] = []
    workflow_data: Optional[dict] = None


# 日志缓冲区（用于实时日志流）
log_buffer = deque(maxlen=1000)
log_listeners: Set[asyncio.Queue] = set()


def log_handler(record):
    """日志处理器，将日志发送到所有监听者"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": record.levelname,
        "message": record.getMessage(),
        "module": record.name
    }
    log_buffer.append(log_entry)
    
    # 通知所有监听者
    for listener in list(log_listeners):
        try:
            listener.put_nowait(log_entry)
        except:
            # 如果队列已满或已关闭，移除监听者
            log_listeners.discard(listener)


# 添加自定义日志处理器
class StreamLogHandler(logging.Handler):
    def emit(self, record):
        try:
            # 确保记录被格式化
            self.format(record)
            log_handler(record)
        except Exception as e:
            # 避免日志处理器本身出错，但记录错误
            print(f"日志处理器错误: {e}")


stream_handler = StreamLogHandler()
stream_handler.setLevel(logging.DEBUG)  # 降低级别以捕获更多日志
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 添加到根日志记录器，捕获所有模块的日志
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # 降低级别
# 移除现有的处理器，避免重复
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
root_logger.addHandler(stream_handler)

# 也添加到当前logger
if stream_handler not in logger.handlers:
    logger.addHandler(stream_handler)

# 测试日志
logger.info("📋 日志系统初始化完成")
logger.info("🔍 测试日志输出 - 这应该出现在前端")


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回前端页面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GIBH-AGENT-V2 测试界面</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            height: calc(100vh - 40px);
        }
        .panel {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
        }
        .panel h2 {
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }
        .chat-panel {
            grid-column: 1;
        }
        .log-panel {
            grid-column: 2;
        }
        .chat-area {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow-y: auto;
            margin-bottom: 15px;
            background: #fafafa;
            min-height: 300px;
        }
        .log-area {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow-y: auto;
            background: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            min-height: 300px;
        }
        .message {
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 4px;
        }
        .message.user {
            background: #e3f2fd;
            text-align: right;
        }
        .message.assistant {
            background: #f1f8e9;
        }
        .message.error {
            background: #ffebee;
            color: #c62828;
        }
        .log-entry {
            margin-bottom: 5px;
            line-height: 1.5;
        }
        .log-entry.INFO { color: #4CAF50; }
        .log-entry.WARNING { color: #FF9800; }
        .log-entry.ERROR { color: #f44336; }
        .log-entry.DEBUG { color: #2196F3; }
        .input-area {
            display: flex;
            gap: 10px;
        }
        input[type="text"], input[type="file"] {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        button {
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        button:hover {
            background: #45a049;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .file-info {
            margin-top: 10px;
            padding: 10px;
            background: #fff3cd;
            border-radius: 4px;
            font-size: 12px;
        }
        .analysis-result {
            background: #f1f8e9 !important;
        }
        .analysis-summary {
            padding: 15px;
        }
        .analysis-summary h3 {
            margin-top: 0;
            color: #4CAF50;
        }
        .analysis-summary h4 {
            margin-top: 15px;
            margin-bottom: 10px;
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }
        .analysis-summary ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .analysis-summary li {
            margin: 5px 0;
        }
        .visualization img, .step-plots img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 10px 0;
        }
        .markers-table {
            overflow-x: auto;
        }
        .markers-table table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        .markers-table th, .markers-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .markers-table th {
            background: #f5f5f5;
            font-weight: bold;
        }
        .think-card {
            background: #f1f8e9 !important;
        }
        .think-process {
            margin-bottom: 10px;
        }
        .think-header {
            background: #e8f5e9;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            user-select: none;
            transition: background 0.2s;
        }
        .think-header:hover {
            background: #c8e6c9;
        }
        .think-icon {
            font-size: 18px;
        }
        .think-title {
            flex: 1;
            font-weight: bold;
            color: #2e7d32;
        }
        .think-toggle {
            color: #666;
            font-size: 12px;
        }
        .think-content {
            margin-top: 10px;
            padding: 15px;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #333;
            max-height: 500px;
            overflow-y: auto;
        }
        .final-answer {
            margin-top: 10px;
            padding: 10px;
        }
        .status {
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            margin-bottom: 10px;
        }
        .status.connected { background: #4CAF50; color: white; }
        .status.disconnected { background: #f44336; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="panel chat-panel">
            <h2>💬 对话界面</h2>
            <div id="status" class="status disconnected">未连接</div>
            <div id="chatArea" class="chat-area"></div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="输入消息或上传文件进行分析..." />
                <input type="file" id="fileInput" accept=".h5ad,.mtx,.tsv,.csv" multiple />
                <button id="sendBtn" onclick="sendMessage()">发送</button>
            </div>
            <div id="fileInfo" class="file-info" style="display:none;"></div>
        </div>
        
        <div class="panel log-panel">
            <h2>📋 实时日志</h2>
            <div id="logArea" class="log-area"></div>
            <div style="margin-top: 10px;">
                <button onclick="clearLogs()">清空日志</button>
                <button onclick="toggleAutoScroll()" id="autoScrollBtn">自动滚动: 开启</button>
            </div>
        </div>
    </div>

    <script>
        let autoScroll = true;
        let logEventSource = null;
        
        // 文件上下文管理（记住已上传的文件）
        let uploadedFilesContext = [];
        
        // 文件选择（支持多文件）
        let selectedFiles = [];
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                selectedFiles = files;
                const fileList = files.map(f => `${f.name} (${(f.size / 1024 / 1024).toFixed(2)} MB)`).join('<br>');
                document.getElementById('fileInfo').style.display = 'block';
                document.getElementById('fileInfo').innerHTML = `📁 已选择 ${files.length} 个文件:<br>${fileList}`;
            }
        });

        // 发送消息
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            const btn = document.getElementById('sendBtn');
            
            if (!message && selectedFiles.length === 0) {
                alert('请输入消息或选择文件');
                return;
            }

            btn.disabled = true;
            const fileNames = selectedFiles.length > 0 ? selectedFiles.map(f => f.name).join(', ') : '';
            addMessage('user', message || (fileNames ? `上传文件: ${fileNames}` : ''));

            try {
                let uploadedFiles = [];
                
                // 如果有新选择的文件，先上传所有文件
                if (selectedFiles.length > 0) {
                    for (const file of selectedFiles) {
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        const uploadRes = await fetch('/api/upload', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (!uploadRes.ok) {
                            throw new Error(`文件上传失败: ${file.name}`);
                        }
                        
                        const uploadData = await uploadRes.json();
                        uploadedFiles.push(uploadData);
                        // 添加到上下文
                        uploadedFilesContext.push(uploadData);
                        addMessage('assistant', `✅ 文件上传成功: ${uploadData.file_name}`);
                    }
                } else if (uploadedFilesContext.length > 0) {
                    // 如果没有新文件，使用上下文中的文件
                    uploadedFiles = uploadedFilesContext;
                    addMessage('assistant', `📁 使用已上传的文件: ${uploadedFiles.map(f => f.file_name).join(', ')}`);
                }

                // 发送聊天请求
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message || (uploadedFiles.length > 0 ? '分析这个文件' : ''),
                        history: [],
                        uploaded_files: uploadedFiles
                    })
                });

                if (!response.ok) {
                    throw new Error(`请求失败: ${response.status}`);
                }

                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/json')) {
                    const data = await response.json();
                    
                    if (data.type === 'workflow_config') {
                        // 执行工作流
                        addMessage('assistant', '🚀 开始执行分析流程...');
                        await executeWorkflow(data.workflow_data, data.file_paths);
                    } else {
                        addMessage('assistant', JSON.stringify(data, null, 2));
                    }
                } else {
                    // 流式响应（支持 think 过程提取）
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let fullText = '';
                    let thinkBuffer = '';
                    let isThinking = false;
                    let hasThinkBlock = false;
                    let finalAnswer = '';
                    let thinkStartIndex = -1;
                    
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        fullText += chunk;
                        
                        // 检测 think 开始标签（支持多种格式）
                        const thinkStartPatterns = [
                            /<think>/i,
                            /<think>/i,
                            /<reasoning>/i,
                            /<thought>/i,
                            /<thinking>/i
                        ];
                        
                        for (const pattern of thinkStartPatterns) {
                            const match = fullText.match(pattern);
                            if (match && !hasThinkBlock) {
                                isThinking = true;
                                hasThinkBlock = true;
                                thinkStartIndex = match.index + match[0].length;
                                // 创建 think 卡片
                                if (!document.querySelector('.think-card:last-child .think-process')) {
                                    createThinkCard();
                                }
                                break;
                            }
                        }
                        
                        // 检测 think 结束标签
                        const thinkEndPatterns = [
                            /<\/think>/i,
                            /<\/redacted_reasoning>/i,
                            /<\/reasoning>/i,
                            /<\/thought>/i,
                            /<\/thinking>/i
                        ];
                        
                        for (const pattern of thinkEndPatterns) {
                            const match = fullText.match(pattern);
                            if (match && isThinking) {
                                // 提取 think 内容
                                thinkBuffer = fullText.substring(thinkStartIndex, match.index);
                                updateThinkContent(thinkBuffer);
                                isThinking = false;
                                
                                // 提取 think 标签之后的内容作为最终答案
                                const afterThinkIndex = match.index + match[0].length;
                                finalAnswer = fullText.substring(afterThinkIndex);
                                if (finalAnswer.trim()) {
                                    updateLastMessage('assistant', finalAnswer.trim());
                                }
                                break;
                            }
                        }
                        
                        // 更新显示
                        if (isThinking) {
                            // 在 think 块中，更新 think 内容
                            if (thinkStartIndex >= 0) {
                                thinkBuffer = fullText.substring(thinkStartIndex);
                                updateThinkContent(thinkBuffer);
                            }
                        } else if (hasThinkBlock && !isThinking) {
                            // think 块已结束，更新最终答案
                            if (finalAnswer) {
                                updateLastMessage('assistant', finalAnswer);
                            }
                        } else {
                            // 没有 think 块，直接更新消息
                            updateLastMessage('assistant', fullText);
                        }
                    }
                }
            } catch (error) {
                addMessage('error', `❌ 错误: ${error.message}`);
                console.error(error);
            } finally {
                btn.disabled = false;
                input.value = '';
                // 不清空 selectedFiles，保留文件选择
                // 但清空文件输入框，允许用户重新选择
                document.getElementById('fileInput').value = '';
                // 如果有上下文文件，显示提示
                if (uploadedFilesContext.length > 0) {
                    document.getElementById('fileInfo').style.display = 'block';
                    document.getElementById('fileInfo').innerHTML = `📁 已上传 ${uploadedFilesContext.length} 个文件，可直接输入需求继续分析`;
                } else {
                    document.getElementById('fileInfo').style.display = 'none';
                }
            }
        }

        // 执行工作流
        async function executeWorkflow(workflowData, filePaths) {
            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        workflow_data: workflowData,
                        file_paths: filePaths
                    })
                });

                const data = await response.json();
                
                if (data.status === 'success') {
                    // 美化显示分析结果
                    displayAnalysisResult(data);
                } else {
                    addMessage('error', `❌ 分析失败: ${data.error || '未知错误'}`);
                }
            } catch (error) {
                addMessage('error', `❌ 执行错误: ${error.message}`);
            }
        }
        
        // 美化显示分析结果
        function displayAnalysisResult(data) {
            const resultDiv = document.createElement('div');
            resultDiv.className = 'message assistant analysis-result';
            
            let html = '<div class="analysis-summary">';
            html += '<h3>✅ 分析完成</h3>';
            
            // QC 指标
            if (data.qc_metrics) {
                html += '<div class="qc-metrics">';
                html += '<h4>📊 质量控制指标</h4>';
                html += '<ul>';
                html += `<li>原始细胞数: <strong>${data.qc_metrics.raw_cells || 'N/A'}</strong></li>`;
                html += `<li>原始基因数: <strong>${data.qc_metrics.raw_genes || 'N/A'}</strong></li>`;
                if (data.qc_metrics.filtered_cells) {
                    html += `<li>过滤后细胞数: <strong>${data.qc_metrics.filtered_cells}</strong></li>`;
                }
                if (data.qc_metrics.filtered_genes) {
                    html += `<li>过滤后基因数: <strong>${data.qc_metrics.filtered_genes}</strong></li>`;
                }
                html += '</ul>';
                html += '</div>';
            }
            
            // 步骤详情
            if (data.steps_details && data.steps_details.length > 0) {
                html += '<div class="steps-details">';
                html += '<h4>📋 执行步骤</h4>';
                html += '<ul>';
                data.steps_details.forEach(step => {
                    html += `<li><strong>${step.name || step.tool_id}</strong>: ${step.summary || '完成'}</li>`;
                });
                html += '</ul>';
                html += '</div>';
            }
            
            // 可视化图片
            if (data.final_plot) {
                html += '<div class="visualization">';
                html += '<h4>📈 可视化结果</h4>';
                // 处理图片路径
                let plotUrl = data.final_plot;
                if (!plotUrl.startsWith('http') && !plotUrl.startsWith('/')) {
                    // 如果路径包含 results，直接使用
                    if (plotUrl.includes('results/')) {
                        plotUrl = '/' + plotUrl;
                    } else {
                        plotUrl = '/results/' + plotUrl;
                    }
                }
                html += `<img src="${plotUrl}" alt="UMAP Visualization" style="max-width: 100%; border-radius: 4px; margin-top: 10px;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"><p style="display:none; color: #999;">图片加载失败: ${plotUrl}</p>`;
                html += '</div>';
            }
            
            // 所有步骤的图片
            if (data.steps_details) {
                const plotSteps = data.steps_details.filter(s => s.plot);
                if (plotSteps.length > 0) {
                    html += '<div class="step-plots">';
                    html += '<h4>📊 步骤可视化</h4>';
                    plotSteps.forEach(step => {
                        let plotUrl = step.plot;
                        if (!plotUrl.startsWith('http') && !plotUrl.startsWith('/')) {
                            // 如果路径包含 results，直接使用
                            if (plotUrl.includes('results/')) {
                                plotUrl = '/' + plotUrl;
                            } else {
                                plotUrl = '/results/' + plotUrl;
                            }
                        }
                        html += `<div style="margin: 10px 0;">`;
                        html += `<strong>${step.name || step.tool_id}</strong><br>`;
                        html += `<img src="${plotUrl}" alt="${step.name}" style="max-width: 100%; border-radius: 4px;" onerror="this.style.display='none';">`;
                        html += `</div>`;
                    });
                    html += '</div>';
                }
            }
            
            // Marker 基因表格（如果有）
            const markersStep = data.steps_details?.find(s => s.name === 'local_markers' || s.tool_id === 'local_markers');
            if (markersStep && markersStep.details) {
                html += '<div class="markers-table">';
                html += '<h4>🧬 Marker 基因</h4>';
                // 直接显示 HTML 表格
                html += markersStep.details;
                html += '</div>';
            }
            
            // 诊断信息
            if (data.diagnosis) {
                html += '<div class="diagnosis">';
                html += '<h4>💡 分析诊断</h4>';
                html += `<div style="white-space: pre-wrap;">${data.diagnosis}</div>`;
                html += '</div>';
            }
            
            html += '</div>';
            resultDiv.innerHTML = html;
            
            const chatArea = document.getElementById('chatArea');
            chatArea.appendChild(resultDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        // 添加消息
        function addMessage(role, content) {
            const chatArea = document.getElementById('chatArea');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}`;
            msgDiv.textContent = content;
            chatArea.appendChild(msgDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        // 更新最后一条消息
        function updateLastMessage(role, content) {
            const chatArea = document.getElementById('chatArea');
            const messages = chatArea.querySelectorAll('.message');
            if (messages.length > 0 && messages[messages.length - 1].classList.contains(role)) {
                const lastMsg = messages[messages.length - 1];
                // 如果已经有 think 卡片，更新最终答案部分
                const finalAnswerDiv = lastMsg.querySelector('.final-answer');
                if (finalAnswerDiv) {
                    finalAnswerDiv.textContent = content;
                } else {
                    lastMsg.textContent = content;
                }
            } else {
                addMessage(role, content);
            }
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        // 创建 think 卡片
        function createThinkCard() {
            const chatArea = document.getElementById('chatArea');
            const thinkCard = document.createElement('div');
            thinkCard.className = 'message assistant think-card';
            thinkCard.innerHTML = `
                <div class="think-process">
                    <div class="think-header" onclick="toggleThink(this)">
                        <span class="think-icon">🤔</span>
                        <span class="think-title">DeepSeek 思考过程</span>
                        <span class="think-toggle">▼</span>
                    </div>
                    <div class="think-content" style="display: none;"></div>
                </div>
                <div class="final-answer"></div>
            `;
            chatArea.appendChild(thinkCard);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        // 更新 think 内容
        function updateThinkContent(content) {
            const chatArea = document.getElementById('chatArea');
            const thinkCards = chatArea.querySelectorAll('.think-card');
            if (thinkCards.length > 0) {
                const lastCard = thinkCards[thinkCards.length - 1];
                const thinkContentDiv = lastCard.querySelector('.think-content');
                if (thinkContentDiv) {
                    thinkContentDiv.textContent = content;
                }
            }
        }
        
        // 切换 think 卡片展开/折叠
        function toggleThink(header) {
            const thinkCard = header.closest('.think-process');
            const content = thinkCard.querySelector('.think-content');
            const toggle = header.querySelector('.think-toggle');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                toggle.textContent = '▲';
            } else {
                content.style.display = 'none';
                toggle.textContent = '▼';
            }
        }
        
        // 全局函数，供 HTML 调用
        window.toggleThink = toggleThink;

        // 连接日志流
        function connectLogStream() {
            if (logEventSource) {
                logEventSource.close();
            }

            logEventSource = new EventSource('/api/logs/stream');
            
            logEventSource.onopen = function() {
                document.getElementById('status').textContent = '已连接';
                document.getElementById('status').className = 'status connected';
                addLogEntry({
                    timestamp: new Date().toISOString(),
                    level: 'INFO',
                    message: '日志流连接成功',
                    module: 'client'
                });
            };

            logEventSource.onerror = function(e) {
                document.getElementById('status').textContent = '连接断开';
                document.getElementById('status').className = 'status disconnected';
                console.error('日志流错误:', e);
                // 3秒后重连
                setTimeout(connectLogStream, 3000);
            };

            logEventSource.onmessage = function(event) {
                try {
                    const logEntry = JSON.parse(event.data);
                    // 忽略心跳消息
                    if (logEntry.type !== 'heartbeat') {
                        addLogEntry(logEntry);
                    }
                } catch (e) {
                    console.error('解析日志失败:', e, event.data);
                    // 即使解析失败，也尝试显示原始数据
                    addLogEntry({
                        timestamp: new Date().toISOString(),
                        level: 'ERROR',
                        message: `日志解析失败: ${event.data.substring(0, 100)}`,
                        module: 'client'
                    });
                }
            };
        }

        // 添加日志条目
        function addLogEntry(entry) {
            const logArea = document.getElementById('logArea');
            const logDiv = document.createElement('div');
            logDiv.className = `log-entry ${entry.level}`;
            
            // 格式化时间戳
            const timestamp = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : '';
            logDiv.textContent = `[${timestamp}] [${entry.level}] ${entry.message}`;
            logArea.appendChild(logDiv);
            
            if (autoScroll) {
                logArea.scrollTop = logArea.scrollHeight;
            }
        }

        // 清空日志
        function clearLogs() {
            document.getElementById('logArea').innerHTML = '';
        }

        // 切换自动滚动
        function toggleAutoScroll() {
            autoScroll = !autoScroll;
            document.getElementById('autoScrollBtn').textContent = `自动滚动: ${autoScroll ? '开启' : '关闭'}`;
        }

        // 回车发送
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // 初始化
        connectLogStream();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """文件上传接口"""
    try:
        logger.info(f"📤 收到文件上传: {file.filename}")
        
        # 保存文件
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"✅ 文件保存成功: {file_path}")
        
        return {
            "status": "success",
            "file_id": file.filename,
            "file_name": file.filename,
            "file_path": str(file_path),
            "file_size": len(content)
        }
    except Exception as e:
        logger.error(f"❌ 文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """聊天接口"""
    if not agent:
        error_msg = "智能体未初始化，请检查配置和日志。可能的原因：1) 配置文件路径错误 2) API Key未设置 3) 依赖包缺失"
        logger.error(error_msg)
        logger.error("请检查终端日志中的详细错误信息")
        return JSONResponse(
            status_code=500,
            content={
                "type": "error",
                "error": error_msg,
                "message": "智能体初始化失败，请查看服务器日志获取详细信息"
            }
        )
    
    try:
        logger.info(f"💬 收到聊天请求: {req.message}")
        logger.info(f"📁 上传文件数: {len(req.uploaded_files)}")
        
        # 转换文件路径
        uploaded_files = []
        for file_info in req.uploaded_files:
            file_path = file_info.get("file_path") or UPLOAD_DIR / file_info.get("file_name", "")
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # 检查文件是否存在
            if not file_path.exists():
                logger.warning(f"⚠️ 文件不存在: {file_path}")
            
            uploaded_files.append({
                "name": file_info.get("file_name", ""),
                "path": str(file_path)
            })
        
        logger.info(f"📂 处理文件: {[f['path'] for f in uploaded_files]}")
        
        # 处理查询
        result = await agent.process_query(
            query=req.message,
            history=req.history,
            uploaded_files=uploaded_files
        )
        
        logger.info(f"✅ 处理完成，返回类型: {result.get('type', 'unknown')}")
        
        # 如果是工作流配置，返回 JSON
        if result.get("type") == "workflow_config":
            return JSONResponse(content={
                "type": "workflow_config",
                "workflow_data": result.get("workflow_data"),
                "file_paths": [f["path"] for f in uploaded_files]
            })
        
        # 如果是聊天响应，返回流式
        if result.get("type") == "chat":
            async def generate():
                try:
                    response_iter = result.get("response")
                    if response_iter:
                        async for chunk in response_iter:
                            yield chunk
                except Exception as e:
                    logger.error(f"❌ 流式响应错误: {e}", exc_info=True)
                    yield f"\\n\\n❌ 错误: {str(e)}"
            
            return StreamingResponse(generate(), media_type="text/plain")
        
        # 其他情况返回 JSON
        return JSONResponse(content=result)
        
    except Exception as e:
        error_detail = f"{type(e).__name__}: {str(e)}"
        logger.error(f"❌ 处理失败: {error_detail}", exc_info=True)
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/execute")
async def execute_workflow(request: dict):
    """执行工作流接口"""
    if not agent:
        raise HTTPException(status_code=500, detail="智能体未初始化")
    
    try:
        workflow_data = request.get("workflow_data")
        file_paths = request.get("file_paths", [])
        
        logger.info(f"🚀 开始执行工作流: {len(file_paths)} 个文件")
        
        # 获取 RNA Agent
        rna_agent = agent.agents.get("rna_agent")
        if not rna_agent:
            raise HTTPException(status_code=500, detail="RNA Agent 未找到")
        
        # 设置输出目录
        output_dir = str(RESULTS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(output_dir, exist_ok=True)
        
        # 执行工作流
        report = await rna_agent.execute_workflow(
            workflow_config=workflow_data,
            file_paths=file_paths,
            output_dir=output_dir
        )
        
        logger.info(f"✅ 工作流执行完成: {report.get('status')}")
        
        # 处理图片路径，转换为可访问的 URL
        # 图片保存在 results/run_xxx/ 目录，需要转换为 /results/run_xxx/filename
        if report.get("final_plot"):
            plot_path = report["final_plot"]
            # 确保路径以 /results/ 开头
            if not plot_path.startswith("/results/"):
                if plot_path.startswith("results/"):
                    plot_path = "/" + plot_path
                elif "/" in plot_path:
                    # 如果包含 run_xxx/filename 格式，添加 results 前缀
                    plot_path = f"/results/{plot_path}"
                else:
                    # 如果只是文件名，需要找到对应的 run 目录
                    # 从 output_dir 中提取 run_xxx
                    run_name = os.path.basename(output_dir)
                    plot_path = f"/results/{run_name}/{plot_path}"
            report["final_plot"] = plot_path
        
        # 处理步骤中的图片路径
        if report.get("steps_details"):
            run_name = os.path.basename(output_dir)
            for step in report["steps_details"]:
                if step.get("plot"):
                    plot_path = step["plot"]
                    # 确保路径以 /results/ 开头
                    if not plot_path.startswith("/results/"):
                        if plot_path.startswith("results/"):
                            plot_path = "/" + plot_path
                        elif "/" in plot_path:
                            plot_path = f"/results/{plot_path}"
                        else:
                            plot_path = f"/results/{run_name}/{plot_path}"
                    step["plot"] = plot_path
        
        return JSONResponse(content=report)
        
    except Exception as e:
        logger.error(f"❌ 工作流执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/stream")
async def stream_logs():
    """实时日志流接口（Server-Sent Events）"""
    logger.info("📡 新的日志流连接")
    
    async def event_generator():
        q = asyncio.Queue(maxsize=100)
        log_listeners.add(q)
        
        try:
            # 先发送历史日志
            history_logs = list(log_buffer)[-100:]  # 最近100条
            logger.info(f"📤 发送历史日志: {len(history_logs)} 条")
            for entry in history_logs:
                yield f"data: {json.dumps(entry, ensure_ascii=False)}\\n\\n"
            
            # 实时发送新日志
            while True:
                try:
                    entry = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield f"data: {json.dumps(entry, ensure_ascii=False)}\\n\\n"
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\\n\\n"
        except asyncio.CancelledError:
            logger.info("📡 日志流连接已取消")
        except Exception as e:
            logger.error(f"❌ 日志流错误: {e}", exc_info=True)
        finally:
            log_listeners.discard(q)
            logger.info("📡 日志流连接已关闭")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """获取历史日志"""
    return JSONResponse(content={
        "logs": list(log_buffer)[-limit:],
        "total": len(log_buffer)
    })


if __name__ == "__main__":
    import uvicorn
    import json
    
    port = int(os.getenv("PORT", 8018))
    logger.info(f"🚀 启动服务器，端口: {port}")
    logger.info(f"📁 上传目录: {UPLOAD_DIR.absolute()}")
    logger.info(f"📁 结果目录: {RESULTS_DIR.absolute()}")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True
    )

