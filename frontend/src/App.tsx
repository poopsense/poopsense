import { useEffect, useState } from "react";
import DemoSampleVisual from "./DemoSampleVisual";
import DemoReportContent from "./DemoReportContent";
import "./demo-explanation.css";

type RecordItem = {
  device_id: string;
  session_id: string;
  received_at: string;
  report: string;
  raw_observations: Record<string, { value: string | null }>;
};
type ExamplePayload = {
  session_id: string;
  correlation_id: string;
  observations: Record<string, { value: string | null }>;
};
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, options);
  if (!response.ok)
    throw new Error(
      `请求失败（${response.status}）。请确认本地演示服务已启动。`,
    );
  return response.json();
}
export default function App() {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [shape, setShape] = useState("elongated");
  const [color, setColor] = useState("yellow");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function refresh() {
    const result = await request<RecordItem[]>("/api/demo/records");
    setRecords(result);
    return result;
  }
  useEffect(() => {
    void refresh()
      .then((items) => setSelected(items[0] ?? null))
      .catch((e) => setError(String(e.message)));
  }, []);
  async function create() {
    setBusy(true);
    setError("");
    try {
      const payload = await request<ExamplePayload>("/api/demo/example");
      payload.session_id = `demo_${crypto.randomUUID()}`;
      payload.correlation_id = `cor_${crypto.randomUUID()}`;
      payload.observations.shape.value = shape;
      payload.observations.color.value = color;
      await request("/api/v1/device-sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Device-Key": "public-local-demo-key-not-a-secret-0001",
        },
        body: JSON.stringify(payload),
      });
      const items = await refresh();
      setSelected(
        items.find((item) => item.session_id === payload.session_id) ?? null,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败，请重试。");
    } finally {
      setBusy(false);
    }
  }
  return (
    <main>
      <header>
        <span className="eyebrow">SEE · SMELL · SENSE</span>
        <h1>
          POOPSENSE<span>便知</span>
        </h1>
        <p>从一次记录，了解产品如何工作。</p>
      </header>
      <div className="notice">
        <strong>开源演示 · 合成数据</strong>
        <span>报告为固定示例。此版本不连接真实设备、大模型或线上服务。</span>
      </div>
      <div className="layout">
        <aside>
          <section className="panel">
            <h2>01 / 提交示例</h2>
            <p>选择形状与颜色，模拟一次设备上传。</p>
            <label>
              形状
              <select value={shape} onChange={(e) => setShape(e.target.value)}>
                <option value="elongated">长条形</option>
                <option value="compact">紧实成团</option>
                <option value="scattered">分散颗粒</option>
                <option value="irregular">不规则形状</option>
              </select>
            </label>
            <label>
              颜色
              <select value={color} onChange={(e) => setColor(e.target.value)}>
                <option value="yellow">黄色</option>
                <option value="red">红色</option>
                <option value="green">绿色</option>
                <option value="blue">蓝色</option>
              </select>
            </label>
            <button
              className="primary"
              disabled={busy}
              onClick={() => void create()}
            >
              {busy ? "提交中…" : "提交并查看结果"}
            </button>
            {error && <p role="alert">{error}</p>}
          </section>
          <section className="panel">
            <h2>历史记录</h2>
            <button
              onClick={() => void refresh().catch((e) => setError(e.message))}
            >
              刷新列表
            </button>
            <p className="muted">
              保存在本机演示数据库；不上传云端。显示最近100条。
            </p>
            <nav aria-label="历史记录">
              {records.map((item) => (
                <button
                  aria-pressed={
                    selected?.session_id === item.session_id &&
                    selected?.device_id === item.device_id
                  }
                  key={`${item.device_id}/${item.session_id}`}
                  onClick={() => setSelected(item)}
                >
                  {new Date(item.received_at).toLocaleString("zh-CN")}
                  <small>{item.session_id.slice(-8)} · 合成示例</small>
                </button>
              ))}
            </nav>
          </section>
        </aside>
        <section className="panel result" aria-live="polite">
          <h2>02 / 记录与报告</h2>
          {selected ? (
            <>
              <DemoSampleVisual
                shape={selected.raw_observations.shape.value}
                color={selected.raw_observations.color.value}
              />
              <p className="source">报告来源：固定示例 / fixed_fixture</p>
              <DemoReportContent text={selected.report} />
              <details>
                <summary>查看接口返回的观测字段</summary>
                <pre>{JSON.stringify(selected.raw_observations, null, 2)}</pre>
              </details>
            </>
          ) : (
            <div className="empty">
              <span>?</span>
              <h3>等待第一条示例记录</h3>
              <p>提交后，这里会显示样本卡通与示例报告。</p>
            </div>
          )}
        </section>
      </div>
      <footer>
        公开范围：展示组件、接口示例与本地演示适配层。核心算法、固件与私有数据不在本仓库中。
      </footer>
    </main>
  );
}
