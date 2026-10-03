# 本地演示接口

这是独立演示服务的精简契约，不是生产 API 的完整替代。设备上传/查询路径和头名称参考现行项目；演示列表与固定报告接口为本仓库新增。

所有请求默认发送至 `http://127.0.0.1:8000`。仅使用合成数据，不粘贴真实密钥或样本。本地公开占位键为 `public-local-demo-key-not-a-secret-0001`；它只用于演示请求格式，没有生产认证能力。

| 方法与路径 | 说明 |
|---|---|
| GET /health、/ready | 返回 local_demo、production_ready=false |
| GET /api/demo/example | 获取完整合成请求模板 |
| POST /api/v1/device-sessions | X-Device-Key 头；成功 202，返回 session_id、device_id、duplicate、data_kind、received_at、assessment_status |
| GET /api/v1/devices/{device_id}/sessions/{session_id} | 同一演示键；成功 200，返回该记录观测与接收状态，不返回报告 |
| GET /api/demo/records | 最近100条演示记录，按接收时间倒序；包含固定 report 与 report_source=fixed_fixture |

## 输入与重复请求

以 [合成 JSON](../backend/scripts/request-simulated.json) 为准。可修改四个标识字段及 observations.shape.value / observations.color.value，其余字段必须保持模板值。形状可为 elongated/compact/scattered/irregular；颜色可为 red/green/blue/yellow。标识长度1–100，只允许英文字母、数字、下划线、点和短横线，首位为字母或数字。

`data_kind` 必须为 simulated；`member_candidates` 必须为空；气味为未启用，置信度为空。保留模板时间仅为说明请求格式，历史列表展示 received_at，不把该模板时间说成实时测量时间。此适配层有意不接受完整硬件协议的所有变化。

同一 device_id + session_id、同一 JSON 语义重复提交：202，duplicate=true；不同内容使用同一标识：409，不覆盖原记录。服务端按键排序后的 JSON 比较，客户端归档仍保留请求原始字节。

请求最大1 MiB；拒绝重复 JSON 键、NaN/Infinity、数值溢出和凭据字段。错误返回 `{ "code": "..." }`：401 占位键不匹配，403 来源/Host非允许的本机地址，404 不存在，409 内容冲突，413 请求长度无效，422 演示字段不合规。

## Python 上传客户端

先启动本地后端。PowerShell 示例：

```powershell
$env:POOPSENSE_DEVICE_KEY = 'public-local-demo-key-not-a-secret-0001'
python backend/scripts/reader_device.py check --file backend/scripts/request-simulated.json
python backend/scripts/reader_device.py upload --file backend/scripts/request-simulated.json
python backend/scripts/reader_device.py status --file backend/scripts/request-simulated.json
```

macOS/Linux 使用 `export POOPSENSE_DEVICE_KEY='public-local-demo-key-not-a-secret-0001'`。

客户端 upload 自动先将原始请求保存到本地 reader-outbox，然后上传；默认不自动重试，不跟随重定向。check 只检查 JSON 和基础标识，不代替服务端校验。接口超时可先查 status，避免误认为失败后随意修改同ID内容。

客户端保留通用硬件测试标签的基础语法检查，但本机公开演示服务只接受 simulated，硬件样本请求会被拒绝。实际设备接入和生产鉴权不在本包范围。
