import os
import json
import asyncio
import aiofiles
import pandas as pd
from groq import Groq

from image_postprocessor import process_images_from_output_json
from image_describer_base64 import process_images_from_output_json
from generate_image_metadata import generate_full_image_data

from config import BASE_DIRECTORY, SUBFOLDERS, OUTPUT_DIRECTORY, GROQ_API_KEY, GROQ_MODEL
from extractor import (
    extract_pdf_content,
    extract_markdown_content,
    extract_excel_content,
    extract_ppt_content
)

def ensure_output_structure():
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIRECTORY, "images", "img_summary"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIRECTORY, "images", "img_vision"), exist_ok=True)

async def write_json_async(path, data):
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=2, ensure_ascii=False))

async def process_pdf_file(pdf_path, groq_client):
    pdf_file = os.path.basename(pdf_path)
    print(f" Processing PDF: {pdf_file}")
    try:
        output_json = await extract_pdf_content(pdf_path, groq_client, GROQ_MODEL)
        output_file = os.path.join(OUTPUT_DIRECTORY, pdf_file.replace(".pdf", "_output.json"))
        await write_json_async(output_file, output_json)
        print(f" Saved PDF output: {output_file}")
    except Exception as e:
        print(f" Error processing PDF {pdf_file}: {str(e)}")

async def process_md_file(md_path, groq_client):
    md_file = os.path.basename(md_path)
    print(f" Processing Markdown: {md_file}")
    try:
        output_json = await extract_markdown_content(md_path, groq_client, GROQ_MODEL)
        output_file = os.path.join(OUTPUT_DIRECTORY, md_file.replace(".md", "_output.json"))
        await write_json_async(output_file, output_json)
        print(f" Saved Markdown output: {output_file}")
    except Exception as e:
        print(f" Error processing Markdown {md_file}: {str(e)}")

async def process_excel_file(excel_path, groq_client):
    excel_file = os.path.basename(excel_path)
    print(f" Processing Excel: {excel_file}")
    try:
        output_json = await extract_excel_content(excel_path, groq_client, GROQ_MODEL)
        output_file = os.path.join(OUTPUT_DIRECTORY, excel_file.replace(".xlsx", "_output.json"))
        await write_json_async(output_file, output_json)
        print(f" Saved Excel output: {output_file}")
    except Exception as e:
        print(f" Error processing Excel {excel_file}: {str(e)}")

async def process_ppt_file(ppt_path, groq_client):
    ppt_file = os.path.basename(ppt_path)
    print(f" Processing PPTX: {ppt_file}")
    try:
        output_json = await extract_ppt_content(ppt_path, groq_client, GROQ_MODEL)
        output_file = os.path.join(OUTPUT_DIRECTORY, ppt_file.replace(".pptx", "_output.json"))
        await write_json_async(output_file, output_json)
        print(f" Saved PPTX output: {output_file}")

        # Since process_images_from_output_json is sync, run it in executor to avoid blocking
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, process_images_from_output_json,
                                   groq_client,
                                   GROQ_MODEL,
                                   os.path.join("output", "images"))
    except Exception as e:
        print(f" Error processing PPTX {ppt_file}: {str(e)}")

async def gather_files():
    pdf_files, md_files, excel_files, ppt_files = [], [], [], []
    for subfolder in SUBFOLDERS:
        folder_path = os.path.join(BASE_DIRECTORY, subfolder)
        print(f" Scanning: {folder_path}")
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(".pdf"):
                    pdf_files.append(file_path)
                elif file.lower().endswith(".md"):
                    md_files.append(file_path)
                elif file.lower().endswith(".xlsx"):
                    excel_files.append(file_path)
                elif file.lower().endswith(".pptx"):
                    ppt_files.append(file_path)
    return pdf_files, md_files, excel_files, ppt_files

async def main():
    ensure_output_structure()
    groq_client = Groq(api_key=GROQ_API_KEY)

    pdf_files, md_files, excel_files, ppt_files = await gather_files()

    tasks = []
    tasks.extend(process_pdf_file(pdf) for pdf in pdf_files)
    tasks.extend(process_md_file(md) for md in md_files)
    tasks.extend(process_excel_file(excel) for excel in excel_files)
    tasks.extend(process_ppt_file(ppt) for ppt in ppt_files)

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
