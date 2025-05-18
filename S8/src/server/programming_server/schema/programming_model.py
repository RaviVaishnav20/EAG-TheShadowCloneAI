from pydantic import BaseModel

class PythonCodeInput(BaseModel):
    code: str

class PythonCodeOutput(BaseModel):
    result: str

class ShellCommandInput(BaseModel):
    command: str