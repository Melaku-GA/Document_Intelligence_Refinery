import gradio as gr
import pymupdf
from src.agents.query_agent import RefineryQueryAgent
import os
agent = RefineryQueryAgent()

# def ask_refinery(question):
#     # 1. Agent processes the question
#     # This returns the answer AND the provenance (BBox, Page, File)
#     response = agent.run(question) 
    
#     # 2. Extract BBox info from the ProvenanceChain
#     # Example: {"page": 4, "x0": 100, "y0": 150, "x1": 300, "y1": 200, "file": "data/CPI.pdf"}
#     prov = response["provenance"][0] 
    
#     # 3. Draw the "Hero Shot" on the PDF
#     doc = pymupdf.open(prov["file"])
#     page = doc[prov["page"] - 1]
    
#     # Draw Red Rectangle
#     rect = pymupdf.Rect(prov["x0"], prov["y0"], prov["x1"], prov["y1"])
#     page.add_rect_annot(rect) # Add the red box
    
#     # Render to image for display
#     pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
#     img = pix.tobytes("png")
    
#     return response["answer"], img

def ask_refinery(question):
    response = agent.run(question)
    
    answer = response.get("answer", "I couldn't find an answer.")
    provenance_list = response.get("provenance", [])

    if not provenance_list:
        return answer, None # No image to show

    prov = provenance_list[0]
    
    try:
        # Check if file exists before opening
        if not os.path.exists(prov["file"]):
            return answer, None
            
        doc = pymupdf.open(prov["file"])
        page = doc[prov["page"] - 1]
        
        # Get bbox coordinates, ensuring they're valid
        x0 = float(prov.get("x0", 0) or 0)
        y0 = float(prov.get("y0", 0) or 0)
        x1 = float(prov.get("x1", 100) or 100)
        y1 = float(prov.get("y1", 100) or 100)
        
        # Ensure valid rectangle dimensions
        if x1 <= x0:
            x1 = x0 + 100
        if y1 <= y0:
            y1 = y0 + 100
        
        # Draw Red Rectangle
        rect = pymupdf.Rect(x0, y0, x1, y1)
        if rect.is_empty or rect.is_infinite:
            # Fallback: use full page
            rect = page.rect
        page.add_rect_annot(rect)
        
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        img = pix.tobytes("png")
        return answer, img
    except Exception as e:
        print(f"Drawing Error: {e}")
        return answer, None
    
# Gradio Layout
with gr.Blocks() as demo:
    gr.Markdown("# Ethiopian Financial Refinery Demo")
    with gr.Row():
        with gr.Column():
            query_input = gr.Textbox(label="Ask the Corpus", placeholder="e.g., What was the headline inflation in March 2025?")
            submit_btn = gr.Button("Query Refinery")
            answer_output = gr.Textbox(label="Refinery Answer")
        with gr.Column():
            image_output = gr.Image(label="Provenance (Hero Shot)")

    submit_btn.click(ask_refinery, inputs=query_input, outputs=[answer_output, image_output])

if __name__ == "__main__":
    demo.launch()