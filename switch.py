# requirements: pip install vosk pyaudio

import json
import sys
from vosk import Model, KaldiRecognizer
import pyaudio
import os

class VoskRealTimeSpeechToText:
    def __init__(self, model_path, sample_rate=16000):
        """
        初始化Vosk实时语音识别
        model_path: F:\\test\\vosk-model-small
        sample_rate: 音频采样率（默认16000）
        """
        # 检查模型路径是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型路径不存在: {model_path}\n请确保已下载Vosk模型并放置在正确路径")
        
        # 加载本地模型
        self.model = Model(model_path)
        self.sample_rate = sample_rate
        
        # 创建识别器
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        
        # 初始化音频流
        self.audio = pyaudio.PyAudio()
        
    def start_realtime_transcription(self):
        """
        开始实时语音识别
        """
        print("正在启动实时语音识别...")
        print("请开始说话（按Ctrl+C停止）")
        
        # 打开音频流
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=8192
        )
        
        stream.start_stream()
        
        try:
            while True:
                # 读取音频数据
                data = stream.read(4096, exception_on_overflow=False)
                
                # 如果有音频数据，进行识别
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    if result["text"]:
                        print(f"识别结果: {result['text']}")
                else:
                    # 获取部分识别结果
                    partial_result = json.loads(self.recognizer.PartialResult())
                    if partial_result["partial"]:
                        sys.stdout.write(f"\r正在识别: {partial_result['partial']}")
                        sys.stdout.flush()
                        
        except KeyboardInterrupt:
            print("\n停止实时语音识别")
        finally:
            # 清理资源
            stream.stop_stream()
            stream.close()
            self.audio.terminate()
            
            # 获取最终结果
            final_result = json.loads(self.recognizer.FinalResult())
            if final_result["text"]:
                print(f"最终识别结果: {final_result['text']}")

    def transcribe_continuous_audio(self, audio_file):
        """
        对音频文件进行连续识别（非实时）
        """
        import wave
        
        # 打开音频文件
        wf = wave.open(audio_file, "rb")
        
        # 检查音频格式
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            wf.close()
            raise ValueError("音频文件必须是16位单声道WAV格式")
        
        results = []
        chunk_size = 4096
        content = wf.readframes(chunk_size)
        
        print("开始识别音频文件...")
        
        # 逐块处理音频数据
        while len(content) > 0:
            if self.recognizer.AcceptWaveform(content):
                result = json.loads(self.recognizer.Result())
                if result["text"]:
                    results.append(result["text"])
                    print(f"识别片段: {result['text']}")
            content = wf.readframes(chunk_size)
        
        # 获取最终结果
        final_result = json.loads(self.recognizer.FinalResult())
        if final_result["text"]:
            results.append(final_result["text"])
            print(f"最终片段: {final_result['text']}")
        
        wf.close()
        return " ".join(results).strip()

# 使用示例
if __name__ == "__main__":
    try:
        # 初始化实时语音识别器，使用本地Vosk模型路径
        # 请将下面的路径替换为您实际的Vosk模型路径
        model_path = "F:/test/vosk-model-small"  # 例如: "vosk-model-small-cn-0.22"
        stt = VoskRealTimeSpeechToText(model_path=model_path)
        
        print("请选择模式:")
        print("1. 实时语音识别（麦克风）")
        print("2. 音频文件识别")
        
        choice = input("请输入选择 (1 或 2): ")
        
        if choice == "1":
            # 实时语音识别
            stt.start_realtime_transcription()
        elif choice == "2":
            # 音频文件识别
            audio_file = input("请输入音频文件路径: ")
            result = stt.transcribe_continuous_audio(audio_file)
            print("\n完整识别结果:", result)
        else:
            print("无效选择")
            
    except FileNotFoundError as e:
        print(f"模型文件未找到: {e}")
        print("请确认模型路径正确，并已下载Vosk模型")
    except Exception as e:
        print(f"识别失败: {e}")