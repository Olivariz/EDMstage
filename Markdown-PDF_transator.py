import pymupdf4llm
import pathlib
import os

path = input("Insert path to the PDF ")
try:
    md_text = pymupdf4llm.to_markdown(path)
except FileNotFoundError: ("File not found, retry")

output=input("Insert the name of the output markdown file ")
try:
    pathlib.Path(output).write_bytes(md_text.encode())
except FileExistsError:
    decision = input("File with this name already exists, do you want to overwrite? Y or N")
    if(decision=='Y'):
        os.remove(output)
        pathlib.Path(output).write_bytes(md_text.encode())
print("File created successefully!")