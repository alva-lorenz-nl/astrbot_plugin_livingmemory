# LivingMemory · 对话线隔离版（Community Fork）

> 本仓库是 [lxfight](https://github.com/lxfight-s-Astrbot-Plugins) 所开发的
> [astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory) 的非官方修改版（fork）。
> 原项目版权归原作者所有，本仓库仅在其基础上增加「对话线（Conversation ID）隔离」相关能力。
> 原版文档：<https://lxfight-s-astrbot-plugins.github.io/astrbot_plugin_livingmemory/>

| 项目 | 说明 |
| --- | --- |
| 上游项目 | `lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory` |
| 上游版本基线 | v2.9.0 |
| 本仓库许可 | AGPL-3.0（与上游一致，见 `LICENSE`） |
| 插件名 | `astrbot_plugin_livingmemory`（与上游同名，可直接替换安装） |

---

## ⚠️ 关于本修改版

- **非官方**：本仓库由社区维护，问题请提到本仓库，不要打扰原作者。
- **兼容上游**：未改动数据库表结构，未改动既有配置项语义，可平滑覆盖安装。
- **按 AGPL-3.0 要求**：本仓库完整保留原 `LICENSE`、原作者信息与上游链接，并公开全部修改内容（见下节「相对上游的改动」）。
- **升级注意**：若日后想回到上游版本，直接覆盖安装上游发布包即可；新增的两个配置项会被自动忽略。

---

## ✨ 相对上游的改动

上游的隔离维度是 **会话（Session）** 与 **人格（Persona）**。一个 AstrBot 会话（如某个私聊或某个群）内部可以有多条**对话线**（Conversation），而记忆原本在同一会话的所有对话线之间共享。

本修改版新增第三个维度：**对话线（Conversation ID）隔离**。

- **写入打标**：新记忆写入时，自动把当前对话线的 `conversation_id` 记入 `metadata`。
- **召回过滤**：检索时只放行「当前对话线」的记忆；未被标记对话线的历史记忆按配置决定是否放行。
- **全链路覆盖**：自动召回、Agent 主动检索工具（`recall_long_term_memory`）、主动记忆工具（`memorize_long_term_memory`）均已接入。
- **缓存隔离**：检索缓存 key 加入 `conversation_id`，避免同一会话下不同对话线互相读到对方的缓存结果。
- **向后兼容**：旧记忆没有 `conversation_id`，默认视为「通用记忆」，可通过开关决定是否仍然召回。

### 新增配置项

位于插件配置的 `filtering_settings` 分组下：

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `use_conversation_filtering` | bool | `true` | **按对话线隔离记忆**。开启后新记忆按 `conversation_id` 隔离，不同对话线互不串线；关闭则不做对话线过滤。 |
| `fallback_to_global_conversations` | bool | `true` | **对话线召回兼容公共旧记忆**。开启时，未标记对话线 ID 的历史记忆与通用背景记忆仍会被召回（推荐开启以保护存量记忆）；关闭则只认当前对话线的记忆。 |

### 推荐配置组合

- **想要最彻底的隔离**：`use_conversation_filtering = true` + `fallback_to_global_conversations = false`。
  代价是升级前的老记忆将不再被召回。
- **想保留老记忆、只管住新记忆**（常见选择）：两项都保持 `true`。
  新记忆严格分线，老记忆照常可用，随着时间自然被新记忆稀释。

---

## 📦 安装

1. 将本仓库目录放入 AstrBot 的 `data/plugins/`，目录名保持 `astrbot_plugin_livingmemory`。
2. 重启 AstrBot，在插件管理页确认已加载。
3. 在插件配置中按上文选择隔离策略。

若已安装上游版本，建议先备份 `data/plugin_data/astrbot_plugin_livingmemory/`（记忆数据库），再覆盖。

---

## 🧪 测试

本修改版附带对话线隔离的单元测试：

```bash
python -m pytest tests/test_conversation_isolation.py -q
```

覆盖写入打标、召回过滤、旧记忆放行、缓存 key 隔离等场景。

---

## 📁 目录结构

```text
├── main.py                 # 插件入口
├── _conf_schema.json       # 配置 schema（含新增的两个对话线配置项）
├── metadata.yaml           # 插件元信息
├── core/
│   ├── memory_scope.py     # 可见性判定（会话 / 人格 / 对话线）
│   ├── utils/__init__.py   # get_conversation_id 等上下文解析
│   ├── event_handler_modules/
│   │   ├── memory_recall.py    # 自动召回链路的对话线过滤
│   │   └── memory_reflection.py# 反思沉淀时写入 conversation_id
│   ├── managers/           # 检索引擎（过滤、过采样、缓存 key 隔离）
│   └── tools/              # Agent 工具（search / memorize / agentic_search）
├── tests/test_conversation_isolation.py
├── docs/                   # 上游文档
└── LICENSE                 # AGPL-3.0，原样保留
```

---

## 📄 致谢与出处

- 原作者：**lxfight** — <https://github.com/lxfight-s-Astrbot-Plugins>
- 上游仓库：<https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory>
- 上游文档：<https://lxfight-s-astrbot-plugins.github.io/astrbot_plugin_livingmemory/>
- 许可协议：**GNU Affero General Public License v3.0**，见 `LICENSE`

`README_en.md`、`README_ru.md`、`CHANGELOG.md`、`docs/` 等文件均为上游原文，未做翻译或改动，可能不包含本修改版新增的对话线功能说明。
