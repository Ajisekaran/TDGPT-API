import os
import json
import base64
import asyncio
import aiofiles
from image_caption import describe_image
from config import OUTPUT_DIRECTORY, GROQ_API_KEY, GROQ_MODEL
from groq import Groq

async def encode_image_base64(image_path):
    loop = asyncio.get_running_loop()
    try:
        
        def read_and_encode():
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
                ext = image_path.split('.')[-1]
                return f"data:image/{ext};base64,{encoded}"
        return await loop.run_in_executor(None, read_and_encode)
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

async def process_images_from_output_json(groq_client, model, image_dir):
    img_vision_dir = os.path.join(OUTPUT_DIRECTORY, "images", "img_vision")
    os.makedirs(img_vision_dir, exist_ok=True)

    groq_client = Groq(api_key=GROQ_API_KEY)

    loop = asyncio.get_running_loop()
    files = await loop.run_in_executor(None, lambda: os.listdir(OUTPUT_DIRECTORY))

    for file_name in files:
        if not file_name.endswith("_output.json"):
            continue

        file_path = os.path.join(OUTPUT_DIRECTORY, file_name)
       
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                contents = await f.read()
            data = json.loads(contents)
        except Exception as e:
            print(f"Error reading JSON file {file_path}: {e}")
            continue

        if "slides" in data:
            content_type = "slide"
            content_list = data["slides"]
        elif "pages" in data:
            content_type = "page"
            content_list = data["pages"]
        else:
            continue

        for item in content_list:
            number = item.get("slide_number") or item.get("page_number")
            images = item.get("images", [])

            for idx, img_path in enumerate(images, start=1):
                try:
                    print(f"Describing image from {img_path}")
                    encoded_image = await encode_image_base64(img_path)

                    # describe_image might be sync - run in executor to not block event loop
                    description = await loop.run_in_executor(
                        None,
                        lambda: describe_image(img_path, groq_client, model)
                    )

                    vision_out = {
                        "page_or_slide": number,
                        "image_base64": encoded_image,
                        "description": description
                    }

                    output_filename = f"{os.path.splitext(file_name)[0]}_{content_type}{number}_img{idx}_vision.json"
                    output_path = os.path.join(img_vision_dir, output_filename)

                    # Write output async
                    async with aiofiles.open(output_path, "w", encoding="utf-8") as out_f:
                        await out_f.write(json.dumps(vision_out, indent=2, ensure_ascii=False))

                except Exception as e:
                    print(f"Error processing image {img_path}: {e}")

if __name__ == "__main__":
    import sys
    import asyncio

    groq_client = Groq(api_key=GROQ_API_KEY)
    asyncio.run(process_images_from_output_json(groq_client, GROQ_MODEL, OUTPUT_DIRECTORY))
