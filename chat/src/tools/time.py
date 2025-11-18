from datetime import datetime


def get_time_now_h_m_s() -> str:
    return datetime.now().strftime("%H:%M:%S")