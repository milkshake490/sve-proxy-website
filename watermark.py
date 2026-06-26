from PIL import Image, ImageDraw, ImageFont
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def add_watermark(args):
    input_path, output_path = args
    try:
        img = Image.open(input_path).convert("RGBA")
        width, height = img.size

        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        font_size = int(height * 0.15)
        try:
            font = ImageFont.truetype("arialbd.ttf", size=font_size)
        except:
            font = ImageFont.load_default()

        text = "PROXY"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = (width - text_w) / 2
        y = (height - text_h) / 2

        #Gray at 75% opacity, thick stroke
        draw.text((x, y), text, font=font, fill=(128, 128, 128, 191),
                  stroke_width=9, stroke_fill=(128, 128, 128, 191))

        rotated = overlay.rotate(0)
        watermarked = Image.alpha_composite(img, rotated)
        watermarked.save(output_path, "PNG")
        return output_path, None
    except Exception as e:
        return output_path, str(e)

def batch_watermark():
    input_dir = "./all_cards_numbered"
    output_dir = "./watermarked_cards"
    os.makedirs(output_dir, exist_ok=True)

    tasks = []
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".png"):
            tasks.append((
                os.path.join(input_dir, filename),
                os.path.join(output_dir, filename)
            ))

    total = len(tasks)
    print(f"Found {total} PNG files in ./all_cards_numbered")
    done = 0
    errors = []

    with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
        futures = {executor.submit(add_watermark, task): task for task in tasks}
        for future in as_completed(futures):
            output_path, error = future.result()
            done += 1
            if error:
                errors.append((output_path, error))
                print(f"[{done}/{total}] ERROR: {os.path.basename(output_path)} — {error}")
            else:
                print(f"[{done}/{total}] Done: {os.path.basename(output_path)}")

    print(f"\nFinished! {total - len(errors)} succeeded, {len(errors)} failed.")
    if errors:
        print("\nFailed files:")
        for path, err in errors:
            print(f"  {path}: {err}")

batch_watermark()