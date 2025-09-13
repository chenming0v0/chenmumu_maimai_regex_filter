"""
RegexFilter 正则过滤插件

一个使用正则表达式处理LLM消息的MaiBot插件，可以对LLM回复进行替换、删除、增添等操作。
"""

import re
from typing import List, Tuple, Type, Optional, Dict, Any
import json
import logging
import os
import toml

from src.plugin_system import (
    BasePlugin,
    register_plugin,
    BaseEventHandler,
    EventType,
    PlusCommand,
    CommandArgs,
    ChatType,
    ConfigField,
    ComponentInfo,
    MaiMessages,
)
from src.plugin_system.base.base_event import HandlerResult
from src.config.config import CONFIG_DIR

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器 - 负责读写配置文件"""
    
    def __init__(self, plugin_name: str, config_file_name: str):
        self.plugin_name = plugin_name
        self.config_file_name = config_file_name
        self.config_path = os.path.join(CONFIG_DIR, "plugins", plugin_name, config_file_name)
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return toml.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # 生成TOML内容
            toml_content = self._generate_toml_content(config_data)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(toml_content)
            
            logger.info(f"配置文件已保存: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def _escape_toml_string(self, value: str) -> str:
        """转义TOML字符串中的特殊字符"""
        # 转义双引号和反斜杠
        return value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

    def _generate_toml_content(self, config_data: Dict[str, Any]) -> str:
        """生成带注释的TOML内容"""
        try:
            toml_str = f"# {self.plugin_name} - 自动生成的配置文件\n"
            toml_str += "# 一个使用正则表达式处理LLM消息的MaiBot插件，可以对LLM回复进行替换、删除、增添等操作。\n\n"
            
            # 插件基本配置
            if 'plugin' in config_data:
                toml_str += "# 插件基本配置\n[plugin]\n\n"
                plugin_config = config_data['plugin']
                
                if 'enabled' in plugin_config:
                    toml_str += "# 是否启用插件\n"
                    toml_str += f"enabled = {str(plugin_config['enabled']).lower()}\n\n"
                
                if 'config_version' in plugin_config:
                    toml_str += "# 配置文件版本\n"
                    version = self._escape_toml_string(str(plugin_config["config_version"]))
                    toml_str += f'config_version = "{version}"\n\n'
            
            # 正则过滤规则配置
            if 'rules' in config_data:
                toml_str += "\n# 正则过滤规则配置\n[rules]\n\n"
                rules_config = config_data['rules']
                
                # 替换规则列表
                if 'replace_rules' in rules_config:
                    toml_str += "# 替换规则列表\n"
                    for rule in rules_config['replace_rules']:
                        toml_str += "[[rules.replace_rules]]\n"
                        pattern = self._escape_toml_string(rule.get("pattern", ""))
                        replacement = self._escape_toml_string(rule.get("replacement", ""))
                        toml_str += f'pattern = "{pattern}"\n'
                        toml_str += f'replacement = "{replacement}"\n'
                        toml_str += f'enabled = {str(rule.get("enabled", True)).lower()}\n'
                        toml_str += f'ignore_case = {str(rule.get("ignore_case", False)).lower()}\n'
                        toml_str += f'multiline = {str(rule.get("multiline", False)).lower()}\n'
                        if 'description' in rule:
                            desc = self._escape_toml_string(rule["description"])
                            toml_str += f'description = "{desc}"\n'
                        toml_str += "\n"
                
                # 删除规则列表
                if 'delete_rules' in rules_config:
                    toml_str += "# 删除规则列表\n"
                    for rule in rules_config['delete_rules']:
                        toml_str += "[[rules.delete_rules]]\n"
                        pattern = self._escape_toml_string(rule.get("pattern", ""))
                        toml_str += f'pattern = "{pattern}"\n'
                        toml_str += f'enabled = {str(rule.get("enabled", True)).lower()}\n'
                        toml_str += f'ignore_case = {str(rule.get("ignore_case", False)).lower()}\n'
                        toml_str += f'multiline = {str(rule.get("multiline", False)).lower()}\n'
                        if 'description' in rule:
                            desc = self._escape_toml_string(rule["description"])
                            toml_str += f'description = "{desc}"\n'
                        toml_str += "\n"
                
                # 添加规则列表
                if 'append_rules' in rules_config:
                    toml_str += "# 添加规则列表\n"
                    for rule in rules_config['append_rules']:
                        toml_str += "[[rules.append_rules]]\n"
                        content = self._escape_toml_string(rule.get("content", ""))
                        position = self._escape_toml_string(rule.get("position", "end"))
                        toml_str += f'content = "{content}"\n'
                        toml_str += f'position = "{position}"\n'
                        toml_str += f'enabled = {str(rule.get("enabled", True)).lower()}\n'
                        if 'description' in rule:
                            desc = self._escape_toml_string(rule["description"])
                            toml_str += f'description = "{desc}"\n'
                        toml_str += "\n"
            
            # 高级设置
            if 'advanced' in config_data:
                toml_str += "# 高级设置\n[advanced]\n\n"
                advanced_config = config_data['advanced']
                
                if 'max_content_length' in advanced_config:
                    toml_str += "# 最大处理内容长度\n"
                    toml_str += f"max_content_length = {advanced_config['max_content_length']}\n\n"
                
                if 'log_changes' in advanced_config:
                    toml_str += "# 是否记录更改日志\n"
                    toml_str += f"log_changes = {str(advanced_config['log_changes']).lower()}\n"
            
            return toml_str
        except Exception as e:
            logger.error(f"生成TOML内容时出错: {e}")
            raise


class RegexMessageFilter(BaseEventHandler):
    """消息正则过滤处理器，拦截LLM响应并进行处理"""

    handler_name = "regex_message_filter"
    handler_description = "拦截并处理LLM响应消息的正则过滤器"
    weight = 100  # 高权重，优先处理
    intercept_message = False  # 不拦截，只处理
    init_subscribe = [EventType.AFTER_LLM]  # 监听LLM响应后事件

    def _clean_extra_whitespace(self, content: str) -> str:
        """清理多余的空格和换行"""
        if not content:
            return content
            
        # 去除开头和结尾的空白字符
        content = content.strip()
        
        # 将连续的空白字符（包括换行、空格、制表符）替换为合理的格式
        # 保留段落间的双换行，但清理多余的空白
        content = re.sub(r'\n\s*\n\s*', '\n\n', content)  # 保留段落分隔
        content = re.sub(r'[ \t]+', ' ', content)  # 多个空格/制表符合并为一个空格
        content = re.sub(r'\n[ \t]+', '\n', content)  # 行首的空格清理
        content = re.sub(r'[ \t]+\n', '\n', content)  # 行尾的空格清理
        
        return content.strip()

    async def execute(self, params: dict | None) -> HandlerResult:
        """执行消息过滤处理"""
        try:
            logger.info(f"RegexFilter开始处理消息，参数类型: {type(params)}")
            if params:
                logger.info(f"参数键值: {list(params.keys())}")
            
            # 直接使用ConfigManager加载配置并检查插件是否启用
            config_manager = ConfigManager("regex_filter_plugin", "config.toml")
            config = config_manager.load_config()
            
            plugin_enabled = config.get("plugin", {}).get("enabled", True)
            logger.info(f"插件启用状态: {plugin_enabled}")
            if not plugin_enabled:
                logger.info("插件未启用，跳过处理")
                return HandlerResult(success=True, continue_process=True, message="插件未启用", handler_name=self.handler_name)

            # 检查参数
            if not params:
                logger.warning("params为空")
                return HandlerResult(success=True, continue_process=True, message="参数为空", handler_name=self.handler_name)

            # 获取LLM响应内容
            llm_response = params.get("llm_response")
            if not llm_response:
                logger.warning(f"未找到llm_response，可用参数: {list(params.keys()) if params else 'None'}")
                return HandlerResult(success=True, continue_process=True, message="未找到llm_response", handler_name=self.handler_name)
            
            original_content = llm_response.get("content")
            if not original_content:
                logger.warning("llm_response中没有content字段")
                return HandlerResult(success=True, continue_process=True, message="未找到LLM响应内容", handler_name=self.handler_name)
                
            logger.info("成功获取到LLM响应内容")

            processed_content = original_content
            logger.info(f"开始处理内容，原始长度: {len(original_content)}")

            # 应用替换规则
            replace_rules = config.get("rules", {}).get("replace_rules", [])
            for rule in replace_rules:
                if not rule.get("enabled", True):
                    continue
                
                pattern = rule.get("pattern", "")
                replacement = rule.get("replacement", "")
                flags = 0
                
                if rule.get("ignore_case", False):
                    flags |= re.IGNORECASE
                if rule.get("multiline", False):
                    flags |= re.MULTILINE
                
                try:
                    processed_content = re.sub(pattern, replacement, processed_content, flags=flags)
                except re.error as e:
                    logger.warning(f"正则表达式错误: {pattern} - {e}")

            # 应用删除规则
            delete_rules = config.get("rules", {}).get("delete_rules", [])
            for rule in delete_rules:
                if not rule.get("enabled", True):
                    continue
                
                pattern = rule.get("pattern", "")
                flags = 0
                
                if rule.get("ignore_case", False):
                    flags |= re.IGNORECASE
                if rule.get("multiline", False):
                    flags |= re.MULTILINE
                
                try:
                    processed_content = re.sub(pattern, "", processed_content, flags=flags)
                except re.error as e:
                    logger.warning(f"正则表达式错误: {pattern} - {e}")

            # 应用添加规则
            append_rules = config.get("rules", {}).get("append_rules", [])
            for rule in append_rules:
                if not rule.get("enabled", True):
                    continue
                
                position = rule.get("position", "end")  # "start" or "end"
                content = rule.get("content", "")
                
                if position == "start":
                    processed_content = content + processed_content
                else:  # end
                    processed_content = processed_content + content

            # 最终清理：去除多余的空格和换行
            cleaned_content = self._clean_extra_whitespace(processed_content)
            
            # 如果内容发生变化，更新LLM响应内容
            if cleaned_content != original_content:
                # 更新llm_response中的content
                llm_response["content"] = cleaned_content
                logger.info("已更新llm_response['content']")
                
                # 根据配置决定是否记录详细更改日志
                log_changes = config.get("advanced", {}).get("log_changes", False)
                
                # 总是记录完整的原始内容和处理后的内容
                logger.info("=" * 80)
                logger.info("RegexFilter处理结果:")
                logger.info(f"原始内容长度: {len(original_content)}")
                logger.info(f"处理后长度: {len(cleaned_content)}")
                logger.info("原始内容:")
                logger.info(original_content)
                logger.info("-" * 80)
                logger.info("处理后内容:")
                logger.info(cleaned_content)
                logger.info("=" * 80)
                
                if log_changes:
                    logger.info(f"消息已处理: '{original_content[:100]}...' -> '{cleaned_content[:100]}...'")
                else:
                    logger.info(f"消息已处理，长度从 {len(original_content)} 变为 {len(cleaned_content)}")
                    
                return HandlerResult(success=True, continue_process=True, message="消息处理完成", handler_name=self.handler_name)
            else:
                logger.info("消息内容无变化")
                return HandlerResult(success=True, continue_process=True, message="消息无变化", handler_name=self.handler_name)

        except Exception as e:
            logger.error(f"RegexFilter处理消息时出错: {e}", exc_info=True)
            return HandlerResult(success=False, continue_process=True, message=f"处理错误: {e}", handler_name=self.handler_name)


class RegexListCommand(PlusCommand):
    """显示当前所有正则规则命令"""

    command_name = "regex_list"
    command_description = "显示当前所有正则过滤规则"
    command_aliases = ["rlist", "regex_show", "regex"]
    chat_type_allow = ChatType.ALL
    intercept_message = True

    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        """执行列表显示命令"""
        try:
            # 处理子命令风格：/regex list
            if not args.is_empty():
                subcommand = args.get_first().lower()
                if subcommand != "list" and subcommand != "show":
                    await self.send_text("❌ 未知子命令，使用 /regex list 查看规则列表")
                    return False, "未知子命令", True
            
            # 直接使用ConfigManager加载配置
            config_manager = ConfigManager("regex_filter_plugin", "config.toml")
            config = config_manager.load_config()
            
            replace_rules = config.get("rules", {}).get("replace_rules", [])
            delete_rules = config.get("rules", {}).get("delete_rules", [])
            append_rules = config.get("rules", {}).get("append_rules", [])
            
            plugin_enabled = config.get("plugin", {}).get("enabled", True)
            status = "🟢 启用" if plugin_enabled else "🔴 禁用"
            
            message = f"🔧 RegexFilter 插件状态: {status}\n\n"
            
            # 替换规则
            if replace_rules:
                message += "🔄 替换规则:\n"
                for i, rule in enumerate(replace_rules, 1):
                    enabled = "✅" if rule.get("enabled", True) else "❌"
                    pattern = rule.get("pattern", "")
                    replacement = rule.get("replacement", "")
                    message += f"{i}. {enabled} '{pattern}' -> '{replacement}'\n"
                message += "\n"
            
            # 删除规则
            if delete_rules:
                message += "🗑️ 删除规则:\n"
                for i, rule in enumerate(delete_rules, 1):
                    enabled = "✅" if rule.get("enabled", True) else "❌"
                    pattern = rule.get("pattern", "")
                    message += f"{i}. {enabled} 删除 '{pattern}'\n"
                message += "\n"
            
            # 添加规则
            if append_rules:
                message += "➕ 添加规则:\n"
                for i, rule in enumerate(append_rules, 1):
                    enabled = "✅" if rule.get("enabled", True) else "❌"
                    position = rule.get("position", "end")
                    content = rule.get("content", "")
                    pos_text = "前缀" if position == "start" else "后缀"
                    message += f"{i}. {enabled} {pos_text}添加 '{content}'\n"
                message += "\n"
            
            if not (replace_rules or delete_rules or append_rules):
                message += "📝 暂无配置的规则\n\n"
            
            message += "💡 使用 /regex_add 添加新规则\n"
            message += "💡 使用 /regex_toggle 切换插件状态"
            
            await self.send_text(message)
            return True, "显示规则列表成功", True

        except Exception as e:
            logger.error(f"显示规则列表时出错: {e}")
            await self.send_text(f"❌ 显示规则列表失败: {e}")
            return False, f"显示规则列表失败: {e}", True


class RegexAddCommand(PlusCommand):
    """添加新的正则规则命令"""

    command_name = "regex_add"
    command_description = "添加新的正则过滤规则"
    command_aliases = ["radd"]
    chat_type_allow = ChatType.ALL
    intercept_message = True

    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        """执行添加规则命令"""
        try:
            if args.count() < 1:
                help_text = (
                    "📝 使用方法:\n"
                    "/regex_add <模式> [替换内容] - 添加替换规则\n"
                    "/regex_add <模式> - 添加删除规则\n"
                    "/regex_add --append <内容> - 添加后缀规则\n"
                    "/regex_add --prepend <内容> - 添加前缀规则\n\n"
                    "例如:\n"
                    "/regex_add 不可以 可以\n"
                    "/regex_add 问题\n"
                    "/regex_add --append \\n\\n——来自MaiBot"
                )
                await self.send_text(help_text)
                return True, "显示帮助", True

            # 检查是否是添加规则
            if args.has_flag("--append"):
                content = args.get_flag_value("--append") or args.get_remaining()
                if not content:
                    await self.send_text("❌ 请指定要添加的后缀内容")
                    return False, "缺少后缀内容", True
                
                await self._add_append_rule(content, "end")
                return True, "添加后缀规则成功", True

            elif args.has_flag("--prepend"):
                content = args.get_flag_value("--prepend") or args.get_remaining()
                if not content:
                    await self.send_text("❌ 请指定要添加的前缀内容")
                    return False, "缺少前缀内容", True
                
                await self._add_append_rule(content, "start")
                return True, "添加前缀规则成功", True

            else:
                # 普通替换/删除规则
                pattern = args.get_first()
                replacement = args.get_remaining() if args.count() > 1 else None

                # 验证正则表达式
                try:
                    re.compile(pattern)
                except re.error as e:
                    await self.send_text(f"❌ 无效的正则表达式: {e}")
                    return False, f"无效的正则表达式: {e}", True

                if replacement is not None:
                    # 添加替换规则
                    await self._add_replace_rule(pattern, replacement)
                    await self.send_text(f"✅ 成功添加替换规则:\n'{pattern}' -> '{replacement}'")
                else:
                    # 添加删除规则
                    await self._add_delete_rule(pattern)
                    await self.send_text(f"✅ 成功添加删除规则:\n删除 '{pattern}'")

                return True, "添加规则成功", True

        except Exception as e:
            logger.error(f"添加规则时出错: {e}")
            await self.send_text(f"❌ 添加规则失败: {e}")
            return False, f"添加规则失败: {e}", True

    async def _add_replace_rule(self, pattern: str, replacement: str):
        """添加替换规则到配置"""
        config_manager = ConfigManager("regex_filter_plugin", "config.toml")
        config = config_manager.load_config()
        
        # 确保rules节存在
        if 'rules' not in config:
            config['rules'] = {}
        if 'replace_rules' not in config['rules']:
            config['rules']['replace_rules'] = []
        
        # 添加新的替换规则
        new_rule = {
            "pattern": pattern,
            "replacement": replacement,
            "enabled": True,
            "ignore_case": False,
            "multiline": False,
            "description": f"替换'{pattern}'为'{replacement}'"
        }
        config['rules']['replace_rules'].append(new_rule)
        
        # 保存配置
        if config_manager.save_config(config):
            logger.info(f"成功添加替换规则: '{pattern}' -> '{replacement}'")
        else:
            logger.error(f"添加替换规则失败: '{pattern}' -> '{replacement}'")
            raise Exception("保存配置文件失败")

    async def _add_delete_rule(self, pattern: str):
        """添加删除规则到配置"""
        config_manager = ConfigManager("regex_filter_plugin", "config.toml")
        config = config_manager.load_config()
        
        # 确保rules节存在
        if 'rules' not in config:
            config['rules'] = {}
        if 'delete_rules' not in config['rules']:
            config['rules']['delete_rules'] = []
        
        # 添加新的删除规则
        new_rule = {
            "pattern": pattern,
            "enabled": True,
            "ignore_case": False,
            "multiline": False,
            "description": f"删除'{pattern}'"
        }
        config['rules']['delete_rules'].append(new_rule)
        
        # 保存配置
        if config_manager.save_config(config):
            logger.info(f"成功添加删除规则: '{pattern}'")
        else:
            logger.error(f"添加删除规则失败: '{pattern}'")
            raise Exception("保存配置文件失败")

    async def _add_append_rule(self, content: str, position: str):
        """添加附加规则到配置"""
        config_manager = ConfigManager("regex_filter_plugin", "config.toml")
        config = config_manager.load_config()
        
        # 确保rules节存在
        if 'rules' not in config:
            config['rules'] = {}
        if 'append_rules' not in config['rules']:
            config['rules']['append_rules'] = []
        
        # 添加新的附加规则
        position_name = "前缀" if position == "start" else "后缀"
        new_rule = {
            "content": content,
            "position": position,
            "enabled": True,
            "description": f"{position_name}添加'{content}'"
        }
        config['rules']['append_rules'].append(new_rule)
        
        # 保存配置
        if config_manager.save_config(config):
            logger.info(f"成功添加{position_name}规则: {content}")
        else:
            logger.error(f"添加{position_name}规则失败: {content}")


class RegexRemoveCommand(PlusCommand):
    """删除指定的正则规则命令"""

    command_name = "regex_remove"
    command_description = "删除指定索引的正则过滤规则"
    command_aliases = ["rdel", "regex_delete"]
    chat_type_allow = ChatType.ALL
    intercept_message = True

    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        """执行删除规则命令"""
        try:
            if args.is_empty():
                await self.send_text("❌ 请指定要删除的规则索引\n使用 /regex_list 查看所有规则")
                return False, "缺少规则索引", True

            rule_type = args.get_first()
            if rule_type not in ["replace", "delete", "append"]:
                await self.send_text("❌ 规则类型必须是: replace, delete, append")
                return False, "无效的规则类型", True

            if args.count() < 2:
                await self.send_text("❌ 请指定要删除的规则索引")
                return False, "缺少规则索引", True

            try:
                index = int(args.get_args()[1]) - 1  # 转换为0基索引
            except ValueError:
                await self.send_text("❌ 规则索引必须是数字")
                return False, "无效的规则索引", True

            # 实现真正的删除逻辑
            success = await self._delete_rule(rule_type, index)
            if success:
                await self.send_text(f"✅ 已删除 {rule_type} 规则 #{index + 1}")
                return True, "删除规则成功", True
            else:
                await self.send_text(f"❌ 删除规则失败，可能索引超出范围")
                return False, "删除规则失败", True

        except Exception as e:
            logger.error(f"删除规则时出错: {e}")
            await self.send_text(f"❌ 删除规则失败: {e}")
            return False, f"删除规则失败: {e}", True

    async def _delete_rule(self, rule_type: str, index: int) -> bool:
        """删除指定类型和索引的规则"""
        config_manager = ConfigManager("regex_filter_plugin", "config.toml")
        config = config_manager.load_config()
        
        rule_key = f"{rule_type}_rules"
        
        if 'rules' not in config or rule_key not in config['rules']:
            return False
        
        rules_list = config['rules'][rule_key]
        
        if index < 0 or index >= len(rules_list):
            return False
        
        # 删除指定索引的规则
        deleted_rule = rules_list.pop(index)
        logger.info(f"删除了{rule_type}规则 #{index + 1}: {deleted_rule}")
        
        # 保存配置
        success = config_manager.save_config(config)
        if not success:
            logger.error(f"删除{rule_type}规则后保存配置失败")
        
        return success


class RegexToggleCommand(PlusCommand):
    """切换插件启用/禁用状态命令"""

    command_name = "regex_toggle"
    command_description = "切换RegexFilter插件的启用/禁用状态"
    command_aliases = ["rtoggle"]
    chat_type_allow = ChatType.ALL
    intercept_message = True

    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        """执行切换状态命令"""
        try:
            # 直接使用ConfigManager加载配置
            config_manager = ConfigManager("regex_filter_plugin", "config.toml")
            config = config_manager.load_config()
            
            current_status = config.get("plugin", {}).get("enabled", True)
            new_status = not current_status
            
            # 实现真正的状态切换
            success = await self._toggle_plugin_status(new_status)
            
            if success:
                status_text = "启用" if new_status else "禁用"
                emoji = "🟢" if new_status else "🔴"
                await self.send_text(f"{emoji} RegexFilter插件已{status_text}")
                return True, f"插件状态切换为{status_text}", True
            else:
                await self.send_text("❌ 切换插件状态失败")
                return False, "切换插件状态失败", True

        except Exception as e:
            logger.error(f"切换插件状态时出错: {e}")
            await self.send_text(f"❌ 切换插件状态失败: {e}")
            return False, f"切换插件状态失败: {e}", True

    async def _toggle_plugin_status(self, new_status: bool) -> bool:
        """切换插件启用状态"""
        config_manager = ConfigManager("regex_filter_plugin", "config.toml")
        config = config_manager.load_config()
        
        # 确保plugin节存在
        if 'plugin' not in config:
            config['plugin'] = {}
        
        # 更新状态
        config['plugin']['enabled'] = new_status
        
        # 保存配置
        if config_manager.save_config(config):
            status_text = "启用" if new_status else "禁用"
            logger.info(f"插件状态已切换为: {status_text}")
            return True
        else:
            logger.error("切换插件状态时保存配置失败")
            return False


class RegexTestCommand(PlusCommand):
    """测试正则规则对指定文本的效果命令"""

    command_name = "regex_test"
    command_description = "测试正则过滤规则对指定文本的处理效果"
    command_aliases = ["rtest"]
    chat_type_allow = ChatType.ALL
    intercept_message = True

    async def execute(self, args: CommandArgs) -> Tuple[bool, Optional[str], bool]:
        """执行测试规则命令"""
        try:
            if args.is_empty():
                await self.send_text("❌ 请提供要测试的文本\n例如: /regex_test 这个问题不可以解决")
                return False, "缺少测试文本", True

            test_text = args.get_raw()
            original_text = test_text

            # 直接使用ConfigManager加载配置并模拟应用规则
            config_manager = ConfigManager("regex_filter_plugin", "config.toml")
            config = config_manager.load_config()
            
            replace_rules = config.get("rules", {}).get("replace_rules", [])
            for rule in replace_rules:
                if not rule.get("enabled", True):
                    continue
                pattern = rule.get("pattern", "")
                replacement = rule.get("replacement", "")
                try:
                    test_text = re.sub(pattern, replacement, test_text)
                except re.error:
                    continue

            delete_rules = config.get("rules", {}).get("delete_rules", [])
            for rule in delete_rules:
                if not rule.get("enabled", True):
                    continue
                pattern = rule.get("pattern", "")
                try:
                    test_text = re.sub(pattern, "", test_text)
                except re.error:
                    continue

            result_message = (
                f"🧪 正则规则测试结果:\n\n"
                f"原始文本:\n{original_text}\n\n"
                f"处理后:\n{test_text}\n\n"
                f"{'✅ 文本已被修改' if test_text != original_text else '❌ 文本未发生变化'}"
            )

            await self.send_text(result_message)
            return True, "测试规则完成", True

        except Exception as e:
            logger.error(f"测试规则时出错: {e}")
            await self.send_text(f"❌ 测试规则失败: {e}")
            return False, f"测试规则失败: {e}", True


@register_plugin
class RegexFilterPlugin(BasePlugin):
    """RegexFilter正则过滤插件"""

    plugin_name = "regex_filter_plugin"
    enable_plugin = True
    dependencies = []
    python_dependencies = []
    config_file_name = "config.toml"

    config_schema = {
        "plugin": {
            "enabled": ConfigField(bool, default=True, description="是否启用插件"),
            "config_version": ConfigField(str, default="1.0.0", description="配置文件版本"),
        },
        "rules": {
            "replace_rules": ConfigField(
                list,
                default=[
                    {
                        "pattern": "不可以",
                        "replacement": "可以",
                        "enabled": True,
                        "ignore_case": False,
                        "multiline": False,
                        "description": "将'不可以'替换为'可以'"
                    },
                    {
                        "pattern": "(糟糕|坏|不好)",
                        "replacement": "好",
                        "enabled": True,
                        "ignore_case": False,
                        "multiline": False,
                        "description": "将负面词汇替换为'好'"
                    }
                ],
                description="替换规则列表"
            ),
            "delete_rules": ConfigField(
                list,
                default=[
                    {
                        "pattern": "问题",
                        "enabled": True,
                        "ignore_case": False,
                        "multiline": False,
                        "description": "删除所有'问题'字样"
                    }
                ],
                description="删除规则列表"
            ),
            "append_rules": ConfigField(
                list,
                default=[],
                description="添加规则列表"
            ),
        },
        "advanced": {
            "max_content_length": ConfigField(int, default=10000, description="最大处理内容长度"),
            "log_changes": ConfigField(bool, default=False, description="是否记录更改日志"),
        },
    }

    config_section_descriptions = {
        "plugin": "插件基本配置",
        "rules": "正则过滤规则配置",
        "advanced": "高级设置",
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """获取插件组件"""
        components = []

        if self.get_config("plugin.enabled", True):
            # 添加消息过滤处理器
            components.append((RegexMessageFilter.get_handler_info(), RegexMessageFilter))
            
            # 添加命令组件
            components.append((RegexListCommand.get_plus_command_info(), RegexListCommand))
            components.append((RegexAddCommand.get_plus_command_info(), RegexAddCommand))
            components.append((RegexRemoveCommand.get_plus_command_info(), RegexRemoveCommand))
            components.append((RegexToggleCommand.get_plus_command_info(), RegexToggleCommand))
            components.append((RegexTestCommand.get_plus_command_info(), RegexTestCommand))

        return components
