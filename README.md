# RegexFilter 正则过滤插件

## 概述

RegexFilter是一个专业的MaiBot消息处理插件，使用正则表达式对LLM回复进行智能过滤和格式化处理。支持替换、删除、添加等多种处理模式，让你的机器人回复更加符合预期。

## 核心功能

### 🔄 消息替换
- 使用正则表达式替换LLM回复中的特定内容
- 支持复杂的正则模式匹配
- 可配置大小写敏感和多行模式

### 🗑️ 内容删除  
- 删除不想要的词汇或短语
- 支持正则表达式模式匹配
- 灵活的过滤规则配置

### ➕ 内容添加
- 在消息前缀或后缀添加自定义内容
- 支持添加签名、免责声明等
- 可配置添加位置

### ⚙️ 实时管理
- 通过聊天命令动态管理规则
- 实时启用/禁用插件功能
- 测试规则效果预览

## 安装说明

插件已经安装在：
- **插件文件**: `plugins/regex_filter_plugin/plugin.py`
- **配置文件**: `config/plugins/regex_filter_plugin/config.toml`  
- **清单文件**: `plugins/regex_filter_plugin/_manifest.json`

## 使用方法

### 基本命令

#### 查看规则列表
```
/regex_list
/regex
```
显示当前所有配置的过滤规则和插件状态。

#### 添加规则
```bash
# 添加替换规则
/regex_add 不可以 可以

# 添加删除规则  
/regex_add 问题

# 添加后缀
/regex_add --append "\n\n——来自MaiBot"

# 添加前缀
/regex_add --prepend "【AI回复】"
```

#### 删除规则
```bash
# 删除替换规则的第1条
/regex_remove replace 1

# 删除删除规则的第2条  
/regex_remove delete 2

# 删除添加规则的第1条
/regex_remove append 1
```

#### 插件控制
```bash
# 切换插件启用/禁用状态
/regex_toggle

# 测试规则效果
/regex_test 这个问题不可以解决
```

### 配置文件

插件配置文件位于 `config/plugins/regex_filter_plugin/config.toml`：

```toml
# 插件基本配置
[plugin]
enabled = true
config_version = "1.0.0"

# 正则过滤规则配置  
[rules]

# 替换规则
[[rules.replace_rules]]
pattern = "不可以"
replacement = "可以"
enabled = true
ignore_case = false
multiline = false
description = "将'不可以'替换为'可以'"

# 删除规则
[[rules.delete_rules]]
pattern = "问题"
enabled = true
ignore_case = false
multiline = false
description = "删除所有'问题'字样"

# 添加规则  
[[rules.append_rules]]
content = "\n\n——来自MaiBot"
position = "end"
enabled = true
description = "添加机器人签名"

# 高级设置
[advanced]
max_content_length = 10000
log_changes = false
```

## 配置说明

### 插件配置 `[plugin]`
- `enabled`: 是否启用插件 (true/false)
- `config_version`: 配置文件版本

### 规则配置 `[rules]`

#### 替换规则 `replace_rules`
- `pattern`: 正则表达式模式
- `replacement`: 替换内容
- `enabled`: 是否启用此规则
- `ignore_case`: 是否忽略大小写
- `multiline`: 是否多行模式
- `description`: 规则描述

#### 删除规则 `delete_rules`  
- `pattern`: 要删除内容的正则表达式
- `enabled`: 是否启用此规则
- `ignore_case`: 是否忽略大小写
- `multiline`: 是否多行模式
- `description`: 规则描述

#### 添加规则 `append_rules`
- `content`: 要添加的内容
- `position`: 添加位置 ("start"前缀 / "end"后缀)
- `enabled`: 是否启用此规则
- `description`: 规则描述

### 高级设置 `[advanced]`
- `max_content_length`: 最大处理内容长度
- `log_changes`: 是否记录详细更改日志

## 正则表达式示例

### 简单文本替换
```toml
[[rules.replace_rules]]
pattern = "不好"
replacement = "很好"
```

### 复杂模式匹配
```toml
[[rules.replace_rules]]
pattern = "(糟糕|坏|不好)"
replacement = "好"
description = "将负面词汇替换为正面词汇"
```

### 删除特定格式
```toml
[[rules.delete_rules]]
pattern = "\\[\\d{4}-\\d{2}-\\d{2}\\]"
description = "删除日期标记如[2024-01-01]"
```

## 工作原理

1. **事件监听**: 插件监听 `POST_LLM` 事件，在LLM生成回复后进行处理
2. **规则应用**: 按照替换→删除→添加的顺序应用规则
3. **内容更新**: 将处理后的内容更新到消息对象
4. **日志记录**: 根据配置记录处理过程和结果

## 性能优化

- 高效的正则表达式编译和缓存
- 可配置的最大内容长度限制
- 智能的规则跳过机制（禁用的规则不会执行）
- 异常处理确保单个规则错误不影响整体功能

## 故障排除

### 常见问题

1. **命令执行失败**: 检查命令格式是否正确
2. **规则不生效**: 确认插件已启用且规则已启用
3. **正则表达式错误**: 使用 `/regex_test` 命令测试规则
4. **配置文件损坏**: 删除配置文件让系统重新生成

### 调试方法

1. 使用 `/regex_test` 命令测试规则效果
2. 查看插件日志获取详细错误信息  
3. 检查配置文件格式是否正确
4. 确认正则表达式语法正确

## 版本信息

- **插件版本**: 1.0.0
- **配置版本**: 1.0.0
- **兼容系统**: MaiBot 0.10.0+

## 更新日志

### v1.0.0 (当前版本)
- ✅ 实现基础的正则过滤功能
- ✅ 支持替换、删除、添加三种处理模式
- ✅ 提供完整的命令行管理接口
- ✅ 实现配置文件的读写和管理
- ✅ 修复了插件系统的基础bug
- ✅ 优化错误处理和日志记录

## 技术支持

如有问题或建议，请：
1. 检查本文档的故障排除部分
2. 查看系统日志获取详细错误信息
3. 提交issue到项目仓库

---

**注意**: 请谨慎使用正则表达式，错误的模式可能导致意外的内容修改。建议先使用 `/regex_test` 命令测试规则效果。

by - chengming0v0 and 克4.1op