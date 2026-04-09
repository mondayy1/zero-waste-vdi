import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

tools = [
    {
        "name": "create_vdi",
        "description": "VDI VM을 생성합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cpu": {
                    "type": "integer",
                    "description": "CPU 코어 수 (1-8)",
                    "minimum": 1,
                    "maximum": 8
                },
                "ram": {
                    "type": "integer",
                    "description": "RAM 크기 MB 단위 최대 8192",
                    "minimum": 512,
                    "maximum": 8192
                },
                "purpose": {
                    "type": "string",
                    "description": "VM 용도 (qa, dev, test 등)"
                }
            },
            "required": ["cpu", "ram", "purpose"]
        }
    }
]

def parse_vdi_request(user_request):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": f"다음 VDI 요청을 분석해서 create_vdi 툴을 호출해줘: {user_request}"
            }
        ]
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "create_vdi":
            return block.input

    return None
