# PoopSense · 便知

让每次排便留下可回看的记录。

PoopSense 是一个面向家庭的智能硬件项目。我们把马桶侧采集与 Web 记录界面连接起来，希望减少手动记录的负担，让用户更容易了解自己的排便变化。

**[项目原型](https://poopsense.org) · [本地体验](#本地运行) · [设备接口](docs/API.md) · [系统结构](docs/ARCHITECTURE.md) · [反馈问题](https://github.com/poopsense/poopsense/issues)**

<p align="center">
  <img src="frontend/public/poop-shape-elongated-yellow-v2.webp" width="190" alt="长条形样本卡通" />
  <img src="frontend/public/poop-shape-compact-yellow-v2.webp" width="190" alt="紧实成团样本卡通" />
  <img src="frontend/public/poop-shape-scattered-yellow-v2.webp" width="190" alt="分散颗粒样本卡通" />
</p>

<p align="center">用形状与颜色呈现一次观测，保留原始字段供用户回看。</p>

## 可以体验什么

这个仓库开放了记录展示组件、设备上传客户端和本地演示服务。不需要硬件或模型账户，就能运行以下流程：

1. 选择一种形状和颜色，提交一条合成记录。
2. 查看对应卡通、观测字段和报告排版。
3. 从历史列表重新打开记录；刷新页面、重启服务后数据仍然保留。

本地报告使用固定示例，界面会标明来源。项目中的传感算法、固件和模型服务独立维护，不随本仓库发布。

## 项目原型的进展

项目原型已接通设备记录上传、形状与颜色展示、真实模型生成结构化报告，以及保存和回看。报告包含本次观察、日常建议和待补充问题；服务端校验观测事实，并保存生成版本。公开示例使用固定报告，便于没有模型账户的开发者运行界面。

任务路由、任务状态追踪和行动跟进模块已有实现。当前手动采样演示尚未接通个人补充信息录入与后续行动跟进；MCP、手表及桌宠仍在探索接入。具体完成度与验证范围见[原型状态](docs/PROTOTYPE.md)。

## 本地运行

需要 Python 3.10+、Node.js 22.12+。后端只使用 Python 标准库。

```sh
git clone https://github.com/poopsense/poopsense.git
cd poopsense
python backend/demo_server.py
```

另开一个终端，在仓库目录运行：

```sh
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --strictPort
```

打开 **http://127.0.0.1:5173**，点击“提交并查看结果”。Windows 上也可使用 `py -3` 运行 Python 命令。

后端使用 8000 端口，前端使用 5173 端口。记录保存在 `backend/.demo/sessions.sqlite3`，仅保留在本机。详细的上传命令、示例 JSON 和返回字段见[接口说明](docs/API.md)。

## 怎么工作

```text
合成观测 → HTTP 上传 → 本机保存 → 卡通与报告展示 → 历史回看
```

- **React / TypeScript**：样本可视化、Markdown 报告和记录列表。
- **Python / SQLite**：接收合成请求、处理重复上传、保存与查询记录。
- **上传客户端**：归档原始请求，再发送到本机接口；可以按设备和记录 ID 查询接收结果。

形状与颜色直接来自输入标签。报告示例用于体验界面，不随输入生成健康判断。本地服务仅适合开发和演示，不提供生产环境的身份认证与家庭数据隔离。

## 开发

```sh
python -m unittest discover -s backend -p "test_*.py" -v
cd frontend
npm test
npm run build
```

源码位置：

| 目录 | 内容 |
|---|---|
| `frontend/src/` | 界面、展示组件及测试 |
| `frontend/public/` | 样本插画 |
| `backend/demo_server.py` | 本地接口服务 |
| `backend/scripts/` | 上传客户端与合成请求 |
| `docs/` | 接口和系统说明 |

欢迎提交安装问题、界面可用性问题和接口示例改进。反馈时请附运行环境、复现步骤和预期结果，使用合成数据，避免上传真实样本或访问密钥。涉及接口字段变化时，请先开 Issue 讨论兼容性。

## License

代码采用 [MIT](LICENSE) 许可证。品牌名称和插画不构成商标授权。
