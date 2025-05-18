from pydantic import BaseModel

class UrlInput(BaseModel):
    url: str

class MarkdownInput(BaseModel):
    text: str

class MarkdownOutput(BaseModel):
    markdown: str

class FilePathInput(BaseModel):
    file_path: str