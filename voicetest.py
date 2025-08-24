# VoiceTest: 语音输入 + 智能编码系统
# pip3 install openai pydub SpeechRecognition requests vosk pyaudio

import speech_recognition as sr
import os
import time
import json
from datetime import datetime
import requests

class VoiceTestAssistant:
    def __init__(self, use_local_model=True, local_model_url="http://localhost:11434/api/generate"):
        self.r = sr.Recognizer()
        self.use_local_model = use_local_model
        self.local_model_url = local_model_url
        self.local_model_name = "deepseek-r1:1.5b"  # 使用DeepSeek deepseekr1 1.5b模型
        
        # API模式配置（保留作为备选）
        if not use_local_model:
            from openai import OpenAI
            self.client = OpenAI(
                api_key="sk-09cfd797a967412dac2341561be418e6", 
                base_url="https://api.deepseek.com"
            )
        
        self.messages = [
            {"role": "system", "content": """你是一个专业的软件开发助手，专门帮助开发团队:
1. 将自然语言需求转换为代码实现
2. 根据需求生成相应的测试用例
3. 提供代码质量保障建议
4. 回答技术问题并提供最佳实践

请以清晰、结构化的方式输出代码和测试用例，并添加必要的注释说明。"""}
        ]
        self.max_history = 8
    
    def capture_voice_input(self, timeout=10, use_vosk=False, vosk_model_path=None):
        """使用麦克风捕获语音输入"""
        if use_vosk and vosk_model_path:
            try:
                return self._capture_voice_with_vosk(timeout, vosk_model_path)
            except Exception as e:
                print(f"Vosk识别失败，回退到Google识别: {e}")
                # 回退到Google识别
                pass
        
        # 默认使用Google语音识别
        try:
            print(f"请在 {timeout} 秒内开始说话...")
            with sr.Microphone() as source:
                print("正在调整麦克风环境噪声...")
                self.r.adjust_for_ambient_noise(source, duration=1)
                print("请说话...")
                audio = self.r.listen(source, timeout=timeout)
            
            print("正在识别语音...")
            text = self.r.recognize_google(audio, language="zh-CN")
            return text
        except sr.WaitTimeoutError:
            return "未检测到语音输入"
        except sr.UnknownValueError:
            return "无法理解语音内容"
        except sr.RequestError as e:
            return f"语音识别服务错误: {e}"
        except Exception as e:
            return f"语音捕获错误: {str(e)}"
    
    def _capture_voice_with_vosk(self, timeout, model_path):
        """使用Vosk进行离线语音识别"""
        try:
            from vosk import Model, KaldiRecognizer
            import pyaudio
            import json
            
            # 检查模型路径
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Vosk模型路径不存在: {model_path}")
            
            print("正在初始化Vosk语音识别...")
            # 加载本地模型
            model = Model(model_path)
            recognizer = KaldiRecognizer(model, 16000)
            
            # 初始化音频流
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8192
            )
            
            stream.start_stream()
            print(f"Vosk语音识别已启动，请在 {timeout} 秒内说话...")
            
            result_text = ""
            start_time = time.time()
            
            try:
                while time.time() - start_time < timeout:
                    data = stream.read(4096, exception_on_overflow=False)
                    
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        if result["text"]:
                            result_text = result["text"]
                            print(f"识别结果: {result_text}")
                            break  # 识别到内容后立即返回
                    else:
                        partial_result = json.loads(recognizer.PartialResult())
                        if partial_result["partial"]:
                            print(f"\r正在识别: {partial_result['partial']}", end="", flush=True)
                            
            except Exception as e:
                print(f"\nVosk识别过程出错: {e}")
            finally:
                # 清理资源
                stream.stop_stream()
                stream.close()
                audio.terminate()
                
                # 获取最终结果
                if not result_text:
                    final_result = json.loads(recognizer.FinalResult())
                    result_text = final_result["text"]
            
            if result_text:
                return result_text
            else:
                return "未检测到语音输入"
                
        except ImportError:
            raise Exception("请安装Vosk和PyAudio: pip install vosk pyaudio")
        except Exception as e:
            raise Exception(f"Vosk语音识别错误: {str(e)}")
    
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
        
        return self._get_response(prompt)
    
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
        
        return self._get_response(prompt)
    
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
        
        return self._get_response(prompt)
    
    def _get_response(self, prompt):
        """获取响应（支持本地模型和API模式）"""
        self.messages.append({"role": "user", "content": prompt})
        
        # 控制历史消息长度
        if len(self.messages) > self.max_history:
            self.messages = [self.messages[0]] + self.messages[-(self.max_history-1):]
        
        if self.use_local_model:
            return self._get_local_model_response(prompt)
        else:
            return self._get_api_response(prompt)
    
    def _get_local_model_response(self, prompt):
        """获取本地DeepSeek模型响应"""
        try:
            # 构造Ollama API请求
            payload = {
                "model": self.local_model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,  # 降低温度以获得更稳定的输出
                    "max_tokens": 2000,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(
                self.local_model_url,
                json=payload,
                timeout=600  # 10分钟超时，因为本地模型可能需要更多时间
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                self.messages.append({"role": "assistant", "content": content})
                return content
            else:
                return f"本地模型调用错误: {response.status_code} - {response.text}"
        except Exception as e:
            return f"本地模型调用错误: {str(e)}"
    
    def _get_api_response(self, prompt):
        """获取API响应"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=self.messages,
                    stream=False,
                    timeout=60,
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

def process_voice_requirement(use_local_model=True):
    """处理语音需求并生成代码和测试"""
    assistant = VoiceTestAssistant(use_local_model=use_local_model)
    
    print("=== VoiceTest 语音需求处理系统 ===")
    print("请确保已连接麦克风设备")
    
    # 询问用户设置超时时间
    try:
        timeout_input = input("请输入语音输入超时时间（秒，默认10秒）: ").strip()
        timeout = int(timeout_input) if timeout_input else 10
    except ValueError:
        timeout = 10
        print("使用默认超时时间: 10秒")
    
    # 询问是否使用Vosk离线识别
    use_vosk = input("是否使用Vosk离线语音识别？(y/N): ").strip().lower() == 'y'
    vosk_model_path = None
    if use_vosk:
        vosk_model_path = input("请输入Vosk模型路径（留空使用默认路径）: ").strip()
        if not vosk_model_path:
            vosk_model_path = "F:/test/vosk-model-small"  # 默认路径
    
    # 1. 语音转文本
    print("\n1. 正在识别语音...")
    requirement = assistant.capture_voice_input(
        timeout=timeout, 
        use_vosk=use_vosk,
        vosk_model_path=vosk_model_path
    )
    print(f"识别结果: {requirement}")
    
    #这个地方，逻辑有问题，重新修改一下
    # if "错误" in requirement or "未检测到" in requirement or "无法理解" in requirement:
    #     print("语音识别失败，无法继续处理")
    #     return
    if requirement.strip() in ["未检测到语音输入", "无法理解语音内容"] or "错误" in requirement:
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

def process_text_requirement(requirement, use_local_model=True):
    """处理文本需求并生成代码和测试"""
    assistant = VoiceTestAssistant(use_local_model=use_local_model)
    
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

def check_local_model_status(url="http://localhost:11434/api/tags"):
    """检查本地模型服务状态"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("本地模型服务运行中，可用模型:")
            for model in models:
                print(f"  - {model['name']}")
            return True
        else:
            print("本地模型服务未运行")
            return False
    except Exception as e:
        print(f"无法连接到本地模型服务: {e}")
        return False

# 示例使用
if __name__ == "__main__":
    print("VoiceTest - 语音输入 + 智能编码系统")
    print("请选择模型模式:")
    print("1. 本地DeepSeek模型模式")
    print("2. API模式")
    
    mode_choice = input("请选择模式 (1-2): ").strip()
    
    use_local_model = True
    if mode_choice == "1":
        if not check_local_model_status():
            print("请先启动Ollama服务: ollama serve")
            print("并确保已拉取DeepSeek模型: ollama pull deepseek-r1:1.5b")
            exit(1)
        print("使用本地DeepSeek模型模式")
    elif mode_choice == "2":
        use_local_model = False
        print("使用API模式")
    else:
        print("无效选择，默认使用本地DeepSeek模型模式")
        if not check_local_model_status():
            print("本地模型服务未运行，切换到API模式")
            use_local_model = False
    
    print("\n1. 处理语音需求（麦克风输入）")
    print("2. 处理文本需求")
    
    choice = input("请选择模式 (1-2): ").strip()
    
    if choice == "1":
        process_voice_requirement(use_local_model)
    elif choice == "2":
        requirement = input("请输入开发需求: ").strip()
        if requirement:
            process_text_requirement(requirement, use_local_model)
        else:
            print("需求不能为空")
    else:
        print("无效选择")