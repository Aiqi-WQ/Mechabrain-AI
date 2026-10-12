"""输入侧轻量安全过滤：敏感词、超长输入、空输入。"""

BLOCKED_WORDS = {
    "制作炸药", "炸弹教程", "枪支购买", "毒品交易", "博彩网站",
    "代写论文代考", "人肉搜索", "开挂脚本",
}

MAX_INPUT_CHARS = 2000


class InputRejected(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def check_question(text: str) -> str:
    """返回清理后的文本，命中规则抛 InputRejected。"""
    cleaned = (text or "").strip()
    if not cleaned:
        raise InputRejected("问题不能为空")
    if len(cleaned) > MAX_INPUT_CHARS:
        raise InputRejected(f"问题过长，请控制在 {MAX_INPUT_CHARS} 字以内")
    for word in BLOCKED_WORDS:
        if word in cleaned:
            raise InputRejected("该内容不在本助手的服务范围内，请换一个学习问题")
    return cleaned


REFUSAL_FALLBACK = (
    "这个问题超出了当前知识库与资料的范围，我没有可靠依据，不猜答案。\n\n"
    "可以换一种问法：带上课程名或章节（例如「机械原理 第2章 自由度」），"
    "或者把题目原文贴进来，我再按步骤讲一遍。"
)
