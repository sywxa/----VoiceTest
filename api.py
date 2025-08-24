
from openai import OpenAI
import asyncio
import threading
import queue
import time

client = OpenAI(api_key="sk-09cfd797a967412dac2341561be418e6", base_url="https://api.deepseek.com")

class FastChatSession:
    def __init__(self, system_prompt="You are a helpful assistant"):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.max_history_length = 6  # 限制历史消息数量以提高速度
    
    def add_message(self, role, content):
        """快速添加消息，控制历史长度"""
        self.messages.append({"role": role, "content": content})
        
        # 只保留最近几轮对话，加快响应速度
        if len(self.messages) > self.max_history_length:
            # 保留system消息和最近的对话
            self.messages = [self.messages[0]] + self.messages[-(self.max_history_length-1):]
    
    def get_quick_response(self, user_input):
        """快速获取响应"""
        self.add_message("user", user_input)
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages,
                stream=False,
                # 设置超时时间
                timeout=10
            )
            
            content = response.choices[0].message.content
            self.add_message("assistant", content)
            return content
        except Exception as e:
            return f"请求出错: {str(e)}"

# 简单快速的对话实现
def simple_fast_chat():
    chat = FastChatSession("你是一个反应迅速的助手，回答要简洁明了")
    
    print("快速对话模式（输入'quit'退出）:")
    
    while True:
        user_input = input("你: ").strip()
        if user_input.lower() == 'quit':
            break
        if not user_input:
            continue
            
        start_time = time.time()
        response = chat.get_quick_response(user_input)
        end_time = time.time()
        
        print(f"助手: {response}")
        print(f"[响应时间: {end_time - start_time:.2f}秒]")
        print("-" * 40)

# 使用线程实现非阻塞对话
class NonBlockingChat:
    def __init__(self, system_prompt="You are a helpful assistant"):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.max_history_length = 6
    
    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        
        if len(self.messages) > self.max_history_length:
            self.messages = [self.messages[0]] + self.messages[-(self.max_history_length-1):]
    
    def get_response_async(self, user_input, callback):
        """异步获取响应"""
        self.add_message("user", user_input)
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=self.messages,
                stream=False,
                timeout=10
            )
            
            content = response.choices[0].message.content
            self.add_message("assistant", content)
            callback(content)
        except Exception as e:
            callback(f"错误: {str(e)}")

def non_blocking_chat():
    chat = NonBlockingChat("你是一个反应迅速的助手，回答要简洁明了")
    response_queue = queue.Queue()
    
    def response_callback(content):
        response_queue.put(content)
    
    print("非阻塞对话模式（输入'quit'退出）:")
    
    while True:
        user_input = input("你: ").strip()
        if user_input.lower() == 'quit':
            break
        if not user_input:
            continue
        
        # 启动线程获取响应
        thread = threading.Thread(
            target=chat.get_response_async,
            args=(user_input, response_callback)
        )
        thread.daemon = True
        thread.start()
        
        print("助手正在思考中...")
        
        # 等待响应，同时可以做其他事情
        try:
            response = response_queue.get(timeout=15)  # 15秒超时
            print(f"助手: {response}")
        except queue.Empty:
            print("助手响应超时")

# 预热连接的快速对话
class PreWarmedChat:
    def __init__(self, system_prompt="You are a helpful assistant"):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.max_history_length = 6
        # 预热连接
        self._warm_up()
    
    def _warm_up(self):
        """预热连接以提高首次响应速度"""
        try:
            client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": "Hi"}],
                stream=False,
                max_tokens=1
            )
        except:
            pass  # 忽略预热错误
    
    def quick_response(self, user_input):
        """快速响应方法"""
        self.messages.append({"role": "user", "content": user_input})
        
        # 限制消息历史长度以提高速度
        if len(self.messages) > self.max_history_length:
            self.messages = [self.messages[0]] + self.messages[-(self.max_history_length-1):]
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=self.messages,
            stream=False,
            timeout=10,
            # 限制输出长度以提高速度
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": content})
        return content

def prewarmed_chat():
    print("预热连接的快速对话（输入'quit'退出）:")
    chat = PreWarmedChat("你是快速响应助手，回答要简洁")
    
    while True:
        user_input = input("你: ").strip()
        if user_input.lower() == 'quit':
            break
        if not user_input:
            continue
            
        start_time = time.time()
        response = chat.quick_response(user_input)
        end_time = time.time()
        
        print(f"助手: {response}")
        print(f"[耗时: {end_time - start_time:.2f}秒]")
        print("-" * 40)

# 运行推荐的快速对话方案
if __name__ == "__main__":
    print("请选择快速对话模式:")
    print("1. 简单快速模式")
    print("2. 非阻塞模式")
    print("3. 预热连接模式")
    
    choice = input("请输入选项 (1-3): ").strip()
    
    if choice == "1":
        simple_fast_chat()
    elif choice == "2":
        non_blocking_chat()
    elif choice == "3":
        prewarmed_chat()
    else:
        print("使用默认的简单快速模式:")
        simple_fast_chat()