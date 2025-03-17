import os
import time
import re
import requests

# 从环境变量中获取相关参数
BAIDU_COOKIE = os.environ.get('BAIDU_COOKIE', '')
# Server酱相关变量
SERVER_PUSH_KEY = os.environ.get('SERVER_PUSH_KEY', '')  # 完整的SendKey
SERVER_UID = os.environ.get('SERVER_UID', '')  # 用户UID

HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': (
        'Mozilla/5.0 (Linux; Android 11; Pixel 5) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 '
        'Mobile Safari/537.36'
    ),
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://pan.baidu.com/wap/svip/growth/task',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
}

final_messages = []


def add_message(msg: str):
    """统一收集消息并打印"""
    print(msg)
    final_messages.append(msg)


def signin():
    """执行每日签到"""
    if not BAIDU_COOKIE.strip():
        add_message("未检测到 BAIDU_COOKIE，请检查环境变量配置。")
        return

    url = "https://pan.baidu.com/rest/2.0/membership/level?app_id=250528&web=5&method=signin"
    signed_headers = HEADERS.copy()
    signed_headers['Cookie'] = BAIDU_COOKIE
    try:
        resp = requests.get(url, headers=signed_headers, timeout=10)
        if resp.status_code == 200:
            sign_point = re.search(r'points":(\d+)', resp.text)
            signin_error_msg = re.search(r'"error_msg":"(.*?)"', resp.text)

            if sign_point:
                add_message(f"签到成功, 获得积分: {sign_point.group(1)}")
            else:
                add_message("签到成功, 但未检索到积分信息")

            # 只有当有错误信息时才输出
            if signin_error_msg and signin_error_msg.group(1):
                add_message(f"签到错误信息: {signin_error_msg.group(1)}")
        else:
            add_message(f"签到失败, 状态码: {resp.status_code}")
    except Exception as e:
        add_message(f"签到请求异常: {e}")


def get_daily_question():
    """获取日常问题"""
    if not BAIDU_COOKIE.strip():
        return None, None

    url = "https://pan.baidu.com/act/v2/membergrowv2/getdailyquestion?app_id=250528&web=5"
    signed_headers = HEADERS.copy()
    signed_headers['Cookie'] = BAIDU_COOKIE
    try:
        resp = requests.get(url, headers=signed_headers, timeout=10)
        if resp.status_code == 200:
            answer = re.search(r'"answer":(\d+)', resp.text)
            ask_id = re.search(r'"ask_id":(\d+)', resp.text)
            if answer and ask_id:
                return answer.group(1), ask_id.group(1)
            else:
                add_message("未找到日常问题或答案")
        else:
            add_message(f"获取日常问题失败, 状态码: {resp.status_code}")
    except Exception as e:
        add_message(f"获取问题请求异常: {e}")
    return None, None


def answer_question(answer, ask_id):
    """回答每日问题"""
    if not BAIDU_COOKIE.strip():
        return

    url = (
        "https://pan.baidu.com/act/v2/membergrowv2/answerquestion"
        f"?app_id=250528&web=5&ask_id={ask_id}&answer={answer}"
    )
    signed_headers = HEADERS.copy()
    signed_headers['Cookie'] = BAIDU_COOKIE
    try:
        resp = requests.get(url, headers=signed_headers, timeout=10)
        if resp.status_code == 200:
            answer_msg = re.search(r'"show_msg":"(.*?)"', resp.text)
            answer_score = re.search(r'"score":(\d+)', resp.text)

            if answer_score:
                add_message(f"答题成功, 获得积分: {answer_score.group(1)}")
            else:
                add_message("答题成功, 但未检索到积分信息")

            # 只有当有答题信息时才输出
            if answer_msg and answer_msg.group(1):
                add_message(f"答题信息: {answer_msg.group(1)}")
        else:
            add_message(f"答题失败, 状态码: {resp.status_code}")
    except Exception as e:
        add_message(f"答题请求异常: {e}")


def get_user_info():
    """获取用户信息"""
    if not BAIDU_COOKIE.strip():
        return

    url = "https://pan.baidu.com/rest/2.0/membership/user?app_id=250528&web=5&method=query"
    signed_headers = HEADERS.copy()
    signed_headers['Cookie'] = BAIDU_COOKIE
    try:
        resp = requests.get(url, headers=signed_headers, timeout=10)
        if resp.status_code == 200:
            current_value = re.search(r'current_value":(\d+)', resp.text)
            current_level = re.search(r'current_level":(\d+)', resp.text)

            level_msg = (
                f"当前会员等级: {current_level.group(1) if current_level else '未知'}, "
                f"成长值: {current_value.group(1) if current_value else '未知'}"
            )
            add_message(level_msg)
        else:
            add_message(f"获取用户信息失败, 状态码: {resp.status_code}")
    except Exception as e:
        add_message(f"用户信息请求异常: {e}")


def send_server_chan(title, message):
    """推送消息到Server酱3"""
    if not SERVER_PUSH_KEY:
        print("未提供Server酱PUSH_KEY，无法发送通知")
        return

    # 如果未提供UID，尝试从PUSH_KEY中提取
    uid = SERVER_UID
    if not uid and SERVER_PUSH_KEY.startswith('sctp'):
        uid_match = re.search(r'^sctp(\d+)t', SERVER_PUSH_KEY)
        if uid_match:
            uid = uid_match.group(1)

    # 如果仍未获得UID，则无法发送通知
    if not uid:
        print("未能获取Server酱UID，无法发送通知。请提供SERVER_UID或确保PUSH_KEY格式正确")
        return

    url = f"https://{uid}.push.ft07.com/send/{SERVER_PUSH_KEY}.send"
    payload = {
        'title': title,
        'desp': message
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            print("Server酱消息发送成功")
        else:
            print("Server酱消息发送失败, 状态码:", resp.status_code)
    except Exception as e:
        print("发送Server酱消息时出现异常:", e)


def main():
    """脚本主流程"""
    signin()
    time.sleep(3)
    answer, ask_id = get_daily_question()
    if answer and ask_id:
        answer_question(answer, ask_id)
    get_user_info()

    # 输出并推送汇总信息
    if final_messages:
        summary_msg = "\n".join(final_messages)
        send_server_chan("百度网盘成长值任务执行结果", summary_msg)


if __name__ == "__main__":
    main()


def handler(event, context):
    main()
