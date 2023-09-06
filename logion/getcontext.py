from .models import Text
import re

def get_context(words, text_id: int, chunk:int) -> [str, str]:
    max_prefix = 100
    max_suffix = 100
    leftIndex = words[0]['index']
    rightIndex = words[-1]['index'] + 1
    text = Text.objects.get(id=text_id)
    chunk_string = text.body.split("***")[chunk]
    chunk_array = re.split('[\s]+', chunk_string)
    # print(chunk_array)
    leftText = chunk_array[:leftIndex]
    leftText = " ".join(leftText)
    rightText = chunk_array[rightIndex:]
    rightText = " ".join(rightText)
    return [leftText, rightText]