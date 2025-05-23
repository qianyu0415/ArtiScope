import requests
import json
import time
import os

def generate_image(prompt, api_key, model="wanx2.1-t2i-turbo", size="1024*1024", n=1):
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "size": size,
            "n": n
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

def check_task_status(task_id, api_key):
    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Task status check failed with status code {response.status_code}: {response.text}")

def save_image_from_url(image_url, save_path):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"图片已保存到: {save_path}")
    else:
        raise Exception(f"图片下载失败: {response.status_code}")

# 独立运行时的主函数
def main():
    api_key = os.getenv('DASHSCOPE_API_KEY', "sk-43024526eeac4da9bc4c85eb1f2dfb2d")
    prompt = "一间有着精致窗户的花店，漂亮的木质门，摆放着花朵"
    
    try:
        # 第一步：创建图像生成任务
        print("正在创建图像生成任务...")
        creation_result = generate_image(prompt, api_key)
        print("任务创建成功，返回结果:")
        print(json.dumps(creation_result, indent=2, ensure_ascii=False))
        
        task_id = creation_result["output"]["task_id"]
        print(f"\n任务ID: {task_id}")
        
        # 第二步：轮询任务状态
        print("\n正在检查任务状态...")
        while True:
            status_result = check_task_status(task_id, api_key)
            task_status = status_result["output"]["task_status"]
            
            print(f"当前状态: {task_status}")
            
            if task_status == "SUCCEEDED":
                print("\n任务完成!")
                # 获取结果URL
                result_url = status_result["output"]["results"][0]["url"]
                print(f"图像URL: {result_url}")
                break
            elif task_status in ["FAILED", "CANCELED"]:
                raise Exception(f"任务失败，状态: {task_status}")
            
            # 等待5秒后再次检查
            time.sleep(5)
        
        # 第三步：下载并保存图像
        save_path = "generated_image.jpg"
        print(f"\n正在下载图像到 {save_path}...")
        save_image_from_url(result_url, save_path)
        
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
