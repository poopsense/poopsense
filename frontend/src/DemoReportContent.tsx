import ChatMessageContent from "./ChatMessageContent";

function Actions({ body }: { body: string }) {
  const parts = body.split(/^### /m);
  const cards = parts.slice(1).map(part => {
    const end = part.indexOf("\n");
    const content = part.slice(end + 1).trim();
    const split = content.indexOf("**怎么做**：");
    return { title: part.slice(0, end), reason: content.slice(0, split).trim(), step: content.slice(split + "**怎么做**：".length).trim(), valid: end > 0 && split >= 0 };
  });
  if (parts[0].trim() || !cards.length || cards.some(card => !card.valid)) return <ChatMessageContent text={body} />;
  return <div className="report-action-grid">{cards.map((card, index) => <article className={`report-action-card action-tone-${index % 4}`} key={`${index}-${card.title}`}>
    <div className="report-action-heading"><span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span><h4>{card.title}</h4></div>
    <ChatMessageContent text={card.step} />
    <details><summary>为什么这样做</summary><ChatMessageContent text={card.reason} /></details>
  </article>)}</div>;
}

export default function DemoReportContent({ text }: { text: string }) {
  // Preserve legacy and unexpected model formatting instead of dropping text.
  if (!text.startsWith("## 本次观察\n")) return <ChatMessageContent text={text} />;
  const sections = text.split(/^## /m).filter(Boolean).map(part => {
    const end = part.indexOf("\n");
    return { title: part.slice(0, end), body: part.slice(end + 1).trim().replaceAll("**怎么做：**", "**怎么做**：") };
  });
  return <div className="demo-report-sections">{sections.map((section, index) => {
    if (section.title === "可以从这些小事开始") return <section className="report-actions-section" key={index} aria-label="日常行动建议">
      <div className="report-section-heading"><small>从一件容易的事开始</small><h3>今天，可以这样照顾自己</h3><p>按自己的情况选择，不必一次完成全部。</p></div>
      <Actions body={section.body} />
    </section>;
    if (section.title === "补充什么，建议会更具体") return <details className="report-context-details" key={index}>
      <summary><span>想让建议更贴近你？<small>还需要了解排便感受和近期生活变化</small></span><span aria-hidden="true">＋</span></summary>
      <p className="report-context-note">以下是待了解的问题，当前报告尚未使用这些个人信息。</p><ChatMessageContent text={section.body} />
    </details>;
    return <section className={`demo-report-section ${index === 0 ? "report-observation" : section.title.includes("咨询") ? "report-care-note" : ""}`} key={`${index}-${section.title}`}>
      <h3>{section.title === "本次观察" ? "这次记录了什么" : section.title === "下一次怎么观察" ? "下次，留意这些变化" : section.title}</h3>
      <ChatMessageContent text={section.body} />
    </section>;
  })}</div>;
}
