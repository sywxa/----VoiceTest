# VoiceTest: 语音输入 + 智能编码系统
# pip3 install openai pydub SpeechRecognition

from openai import OpenAI
import speech_recognition as sr
import tempfile
import os
import time
import json
from datetime import datetime

client = OpenAI(api_key="sk-09cfd797a967412dac2341561be418e6", base_url="https://api.deepseek.com")

class VoiceTestAssistant:
    def __init__(self):
        self.r = sr.Recognizer()
        self.messages = [
            {"role": "system", "content": """你是一个专业的软件开发助手，专门帮助开发团队:
1. 将自然语言需求转换为代码实现
2. 根据需求生成相应的测试用例
3. 提供代码质量保障建议
4. 回答技术问题并提供最佳实践

请以清晰、结构化的方式输出代码和测试用例，并添加必要的注释说明。"""}
        ]
        self.max_history = 8
    
    def transcribe_audio(self, audio_file_path):
        """转录音频文件为文本"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.r.record(source)
            text = self.r.recognize_google(audio, language="zh-CN")
            return text
        except Exception as e:
            return f"语音识别错误: {str(e)}"
    
    def generate_code_from_requirement(self, requirement):
        """根据需求生成代码"""
        prompt = f"""
请根据以下开发需求生成相应的Python代码:

需求描述: {requirement}

要求:
1. 生成完整可运行的Python代码
2. 包含必要的注释说明关键逻辑
3. 遵循Python最佳实践和PEP8规范
4. 如果需求复杂，可以提供模块化设计
5. 代码应具有良好的可读性和可维护性
        """
        
        return self._get_ai_response(prompt)
    
    def generate_test_cases(self, requirement, code=""):
        """根据需求生成测试用例"""
        prompt = f"""
请为以下需求生成相应的测试用例:

需求描述: {requirement}

{f"参考代码: {code}" if code else ""}

要求:
1. 使用Python unittest框架
2. 覆盖主要功能和边界条件
3. 包含正向和负向测试用例
4. 添加必要的注释说明测试目的
5. 测试用例应具有良好的可读性
        """
        
        return self._get_ai_response(prompt)
    
    def code_review_and_suggestions(self, code):
        """代码审查和改进建议"""
        prompt = f"""
请对以下代码进行审查并提供改进建议:

代码内容:
{code}

要求:
1. 指出潜在的问题和改进点
2. 提供代码质量优化建议
3. 检查是否符合最佳实践
4. 给出具体修改方案
        """
        
        return self._get_ai_response(prompt)
    
    def _get_ai_response(self, prompt):
        """获取AI响应"""
        self.messages.append({"role": "user", "content": prompt})
        
        # 控制历史消息长度
        if len(self.messages) > self.max_history:
            self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=self.messages,
                    stream=False,
                    timeout=30,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content
                self.messages.append({"role": "assistant", "content": content})
                return content
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"第{attempt + 1}次尝试失败，{2 ** attempt}秒后重试: {str(e)}")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return f"AI生成错误: {str(e)}"
    
    def save_session(self, filename=None):
        """保存会话记录"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voicetest_session_{timestamp}.json"
        
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "messages": self.messages
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        return filename

def process_voice_requirement(audio_file_path):
    """处理语音需求并生成代码和测试"""
    assistant = VoiceTestAssistant()
    
    print("=== VoiceTest 语音需求处理系统 ===")
    print(f"处理音频文件: {audio_file_path}")
    
    # 1. 语音转文本
    print("\n1. 正在识别语音...")
    requirement = assistant.transcribe_audio(audio_file_path)
    print(f"识别结果: {requirement}")
    
    if "语音识别错误" in requirement:
        print("语音识别失败，无法继续处理")
        return
    
    # 2. 选择处理类型
    print("\n请选择要生成的内容:")
    print("1. 仅生成代码")
    print("2. 仅生成测试用例")
    print("3. 生成代码和测试用例")

    choice = input("请输入选项 (1-3): ").strip()
    
    if choice == "1":
        # 仅生成代码
        print("\n正在生成代码...")
        start_time = time.time()
        code = assistant.generate_code_from_requirement(requirement)
        end_time = time.time()
        print(f"代码生成完成 (耗时: {end_time - start_time:.2f}秒)")
        print("\n生成的代码:")
        print("=" * 50)
        print(code)
        print("=" * 50)
    elif choice == "2":
        # 仅生成测试用例
        print("\n正在生成测试用例...")
        start_time = time.time()
        test_cases = assistant.generate_test_cases(requirement)
        end_time = time.time()
        print(f"测试用例生成完成 (耗时: {end_time - start_time:.2f}秒)")
        print("\n生成的测试用例:")
        print("=" * 50)
        print(test_cases)
        print("=" * 50)
    elif choice == "3":
        # 生成代码和测试用例
        # 生成代码
        print("\n正在生成代码...")
        start_time = time.time()
        code = assistant.generate_code_from_requirement(requirement)
        end_time = time.time()
        print(f"代码生成完成 (耗时: {end_time - start_time:.2f}秒)")
        print("\n生成的代码:")
        print("=" * 50)
        print(code)
        print("=" * 50)
        
        # 生成测试用例
        print("\n正在生成测试用例...")
        start_time = time.time()
        test_cases = assistant.generate_test_cases(requirement, code)
        end_time = time.time()
        print(f"测试用例生成完成 (耗时: {end_time - start_time:.2f}秒)")
        print("\n生成的测试用例:")
        print("=" * 50)
        print(test_cases)
        print("=" * 50)
    else:
        print("无效选择")
        return
    
    # 保存会话
    filename = assistant.save_session()
    print(f"\n会话已保存到: {filename}")

def process_text_requirement(requirement):
    """处理文本需求并生成代码和测试"""
    assistant = VoiceTestAssistant()
    
    print("=== VoiceTest 文本需求处理系统 ===")
    print(f"处理需求: {requirement}")
    
    # 选择处理类型
    print("\n请选择要生成的内容:")
    print("1. 仅生成代码")
    print("2. 仅生成测试用例")
    print("3. 生成代码和测试用例")
    
    choice = input("请输入选项 (1-3): ").strip()
    
    if choice == "1":
        # 仅生成代码
        print("\n正在生成代码...")
        start_time = time.time()
        code = assistant.generate_code_from_requirement(requirement)
        end_time = time.time()
        print(f"代码生成完成 (耗时: {end_time - start_time:.2f}秒)")
        print("\n生成的代码:")
        print("=" * 50)
        print(code)
        print("=" * 50)
    elif choice == "2":
        # 仅生成测试用例
        print("\n正在生成测试用例...")
        start_time = time.time()
        test_cases = assistant.generate_test_cases(requirement)
        end_time = time.time()
        print(f"测试用例生成完成 (耗时: {end_time - start_time:.2f}秒)")
        print("\n生成的测试用例:")
        print("=" * 50)
        print(test_cases)
        print("=" * 50)
    elif choice == "3":
        # 生成代码和测试用例
        # 生成代码
        print("\n正在生成代码...")
        start_time = time.time()
        code = assistant.generate_code_from_requirement(requirement)
        end_time = time.time()
        print(f"代码生成完成 (耗时: {end_time - start_time:.2f}秒)")
        print("\n生成的代码:")
        print("=" * 50)
        print(code)
        print("=" * 50)
        
        # 生成测试用例
        print("\n正在生成测试用例...")
        start_time = time.time()
        test_cases = assistant.generate_test_cases(requirement, code)
        end_time = time.time()
        print(f"测试用例生成完成 (耗时: {end_time - start_time:.2f}秒)")
        print("\n生成的测试用例:")
        print("=" * 50)
        print(test_cases)
        print("=" * 50)
    else:
        print("无效选择")
        return
    
    # 保存会话
    filename = assistant.save_session()
    print(f"\n会话已保存到: {filename}")

# 示例使用
if __name__ == "__main__":
    print("VoiceTest - 语音输入 + 智能编码系统")
    print("1. 处理语音需求")
    print("2. 处理文本需求")
    
    choice = input("请选择模式 (1-2): ").strip()
    
    if choice == "1":
        audio_file = input("请输入音频文件路径: ").strip()
        if os.path.exists(audio_file):
            process_voice_requirement(audio_file)
        else:
            print("音频文件不存在")
    elif choice == "2":
        requirement = input("请输入开发需求: ").strip()
        if requirement:
            process_text_requirement(requirement)
        else:
            print("需求不能为空")
    else:
        print("无效选择")