import azure.cognitiveservices.speech as speechsdk
import time
from datetime import datetime
import statistics

def get_current_time():
    """返回当前时间的格式化字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

class PerformanceMonitor:
    def __init__(self):
        self.latencies = []
        self.recognition_start_times = {}
        self.recognition_results = []
        
    def add_latency(self, latency):
        self.latencies.append(latency)
        
    def add_recognition_start(self, session_id, start_time):
        self.recognition_start_times[session_id] = start_time
        
    def add_recognition_result(self, session_id, text, end_time):
        if session_id in self.recognition_start_times:
            start_time = self.recognition_start_times[session_id]
            duration = end_time - start_time
            self.recognition_results.append({
                'text': text,
                'duration': duration,
                'timestamp': get_current_time()
            })
            
    def print_statistics(self):
        if self.latencies:
            print(f"\n[{get_current_time()}] 性能统计:")
            print(f"  平均延迟: {statistics.mean(self.latencies):.2f}ms")
            print(f"  最小延迟: {min(self.latencies):.2f}ms")
            print(f"  最大延迟: {max(self.latencies):.2f}ms")
            if len(self.latencies) > 1:
                print(f"  延迟标准差: {statistics.stdev(self.latencies):.2f}ms")
        
        if self.recognition_results:
            print(f"\n识别结果统计:")
            avg_duration = statistics.mean([r['duration'] * 1000 for r in self.recognition_results])
            print(f"  平均识别时间: {avg_duration:.2f}ms")

def speech_recognize_continuous():

    # 记录总体启动时间
    total_init_start = time.time()
    print(f"[{get_current_time()}] 开始初始化程序...")

    config_start = time.time()


    # 设置 Azure Speech 配置参数
    subscription_key = ""  # 订阅密钥
    service_region = ""    # 服务区域
    
    # 创建性能监控器
    monitor = PerformanceMonitor()
    
    # 创建 speech 配置对象
    speech_config = speechsdk.SpeechConfig(
        subscription=subscription_key,
        region=service_region
    )
    
    speech_config.speech_recognition_language = "zh-CN"
    
    # 基础优化设置
    speech_config.set_profanity(speechsdk.ProfanityOption.Raw)  
    #speech_config.enable_audio_logging()
    
    # 参数优化 
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "100")  # 降低到100ms
    
    # 构建并输出端点信息
    endpoint_url = f"wss://{service_region}.stt.speech.microsoft.com/speech/universal/v2"
    print(f"[{get_current_time()}] Speech Service Endpoint URL: {endpoint_url}")
    
    # 输出连接详情
    print(f"[{get_current_time()}] Connection Details:")
    print(f"  - Region: {service_region}")
    print(f"  - Recognition Language: {speech_config.speech_recognition_language}")
    print(f"  - Subscription Key: ****{subscription_key[-4:] if len(subscription_key) >= 4 else ''}")
    print(f"  - Silence Timeout: 100ms")

    config_time = time.time() - config_start
    print(f"[{get_current_time()}] Speech配置初始化完成: {config_time*1000:.2f}ms")

    audio_start = time.time()
    print(f"[{get_current_time()}] 开始初始化音频设备...")

    # 创建音频配置
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    audio_time = time.time() - audio_start
    print(f"[{get_current_time()}] 音频设备初始化完成: {audio_time*1000:.2f}ms")

    recognizer_start = time.time()
    print(f"[{get_current_time()}] 开始创建语音识别器...")

    # 创建语音识别器
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    recognizer_time = time.time() - recognizer_start
    print(f"[{get_current_time()}] 语音识别器创建完成: {recognizer_time*1000:.2f}ms")

    # 总初始化时间
    total_init_time = time.time() - total_init_start
    print(f"\n[{get_current_time()}] ===== 初始化时间统计 =====")
    print(f"[{get_current_time()}] Speech配置时间: {config_time*1000:.2f}ms")
    print(f"[{get_current_time()}] 音频设备时间: {audio_time*1000:.2f}ms")
    print(f"[{get_current_time()}] 识别器创建时间: {recognizer_time*1000:.2f}ms")
    print(f"[{get_current_time()}] 总初始化时间: {total_init_time*1000:.2f}ms")

    # 预热连接
    silent_audio = b'\x00' * 16000  # 1秒静音
    audio_stream = speechsdk.audio.PushAudioInputStream()
    audio_stream.write(silent_audio)
    audio_stream.close()
    silent_audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
    silent_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=silent_audio_config)
    silent_recognizer.recognize_once()  # 模型加载

    # 程序启动提示
    print(f"[{get_current_time()}] 程序启动，5秒后开始录音...")

    # 倒计时
    for i in range(3, 0, -1):
        print(f"[{get_current_time()}] 倒计时 {i} 秒...")
        time.sleep(1)

    print(f"[{get_current_time()}] 开始录音，请说话...")

    # 持续时间（秒）
    start_time = time.time()
    recognition_duration = 20  # 识别持续时间（秒）
    
    # 用于计算延迟的变量
    recognition_start_time = None
    first_byte_time = None
    is_first_recognition = True
    current_session_id = 0

    # 处理识别开始的回调函数
    def handle_recognizing(evt):
        nonlocal recognition_start_time, first_byte_time, is_first_recognition, current_session_id
        current_time = time.time()
        
        if evt.result.text:
            current_session_id += 1
            monitor.add_recognition_start(current_session_id, current_time)
            
            if is_first_recognition:
                recognition_start_time = current_time
                first_byte_time = current_time
                is_first_recognition = False
                first_byte_latency = (first_byte_time - start_time) * 1000
                print(f"[{get_current_time()}] First Byte Latency: {first_byte_latency:.2f}ms")
                monitor.add_latency(first_byte_latency)
                print(f"[{get_current_time()}] Recognizing Event: {evt}")


    # 处理识别结果的回调函数
    def handle_result(evt):
        nonlocal recognition_start_time, current_session_id
        current_time = time.time()
        
        if current_time - start_time <= recognition_duration:
            if evt.result.text:
                if recognition_start_time is not None:
                    finish_latency = (current_time - recognition_start_time) * 1000
                    print(f"[{get_current_time()}] 识别结果: {evt.result.text}")
                    print(f"[{get_current_time()}] Finish Latency: {finish_latency:.2f}ms")
                    monitor.add_recognition_result(current_session_id, evt.result.text, current_time)
                    recognition_start_time = None
                else:
                    print(f"[{get_current_time()}] 识别结果: {evt.result.text}")

    # 处理识别结束的回调函数
    def stop_cb(evt):
        print(f"[{get_current_time()}] 会话结束.")
        monitor.print_statistics()
        speech_recognizer.stop_continuous_recognition()

    # 注册回调函数
    speech_recognizer.recognizing.connect(handle_recognizing)
    speech_recognizer.recognized.connect(handle_result)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)



    # 开始连续识别
    speech_recognizer.start_continuous_recognition()

    # 等待识别
    time.sleep(recognition_duration)

    # 停止识别
    speech_recognizer.stop_continuous_recognition()
    print(f"[{get_current_time()}] 录音结束")
    monitor.print_statistics()
    print(f"[{get_current_time()}] 程序退出.")

if __name__ == "__main__":
    try:
        speech_recognize_continuous()
    except Exception as e:
        print(f"[{get_current_time()}] 发生错误: {str(e)}")
