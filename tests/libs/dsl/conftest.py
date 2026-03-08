"""Shared test fixtures for DSL tests."""

from libs.dsl.executor import ActionExecutor


class MockExecutor(ActionExecutor):
    """Mock executor with call tracking and prefixed responses."""

    def __init__(self):
        self.calls: list[dict] = []

    def execute_infer(self, content: str, args: dict[str, str]) -> str:
        self.calls.append({"type": "infer", "content": content, "args": args})
        result = content
        for k, v in args.items():
            result = result.replace(f"{{{k}}}", v)
        return f"[推理结果] {result}"

    def execute_lambda(self, content: str, input_text: str) -> str:
        self.calls.append({"type": "lambda", "content": content, "input": input_text})
        return f"[Lambda结果] {content}"


class PassthroughExecutor(ActionExecutor):
    """Executor that returns content as-is (no prefix). For integration tests."""

    def execute_infer(self, content: str, args: dict[str, str]) -> str:
        result = content
        for k, v in args.items():
            result = result.replace(f"{{{k}}}", v)
        return result

    def execute_lambda(self, content: str, input_text: str) -> str:
        return content
