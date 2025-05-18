from src.server.rag_server.schema.rag_model import UrlInput, MarkdownOutput, FilePathInput
import trafilatura
import pymupdf4llm
import os
import re
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.server.rag_server.common.config.rag_config import GLOBAL_IMAGE_DIR
from src.server.rag_server.common.utils import replace_images_with_captions
from src.common.logger.logger import get_logger

logger = get_logger()   
def extract_webpage(input: UrlInput) -> MarkdownOutput:
    """Extract and convert webpage content to markdown. Usage: extract_webpage|input={"url": "https://example.com"}"""
    
    downloaded = trafilatura.fetch_url(input.url)
    if not downloaded:
        return MarkdownOutput(markdown="Failed to download the webpage.")
    
    markdown = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        include_images=True,
        output_format='markdown'
    ) or ""
    
    markdown = replace_images_with_captions(markdown)
    return MarkdownOutput(markdown=markdown)


def extract_pdf(input: FilePathInput) -> MarkdownOutput:
    """Convert PDF file content to markdown format. Usage: extract_pdf|input={"file_path": "documents/dlf.pdf"}"""

    if not os.path.exists(input.file_path):
        return MarkdownOutput(markdown=f"File not found: {input.file_path}")
    
    global_image_dir = GLOBAL_IMAGE_DIR
    global_image_dir.mkdir(parents=True, exist_ok=True)

    markdown = pymupdf4llm.to_markdown(
        input.file_path,
        write_images = True,
        image_path = str(global_image_dir)
    )

    #Re-point image links in the markdown
    markdown = re.sub(
        r'!\[\]\((.*?/images/)([^)]+)\)',
        r'![](images/\2)',
        markdown.replace("\\", "/")
    )
        
    markdown = replace_images_with_captions(markdown)
    return MarkdownOutput(markdown=markdown)