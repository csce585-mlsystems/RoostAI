from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
from huggingface_hub import login


def test_model_setup(model_name="mistralai/Mixtral-8x7B-Instruct-v0.1"):
    """Test if model can be downloaded and loaded."""
    print(f"\n1. Testing model download and setup for: {model_name}")
    
    try:
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        print("Loading model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="cpu",
        )
        print("✓ Model and tokenizer loaded successfully!")
        return model, tokenizer
    
    except Exception as e:
        print(f"✗ Error loading model: {str(e)}")
        return None, None


def test_inference(model, tokenizer):
    """Test if model can perform inference on a small sample."""
    print("\n2. Testing inference with a small sample")
    
    # Sample document and chunk
    sample_document = """This is a research paper about climate change.
    The paper discusses the effects of greenhouse gases on global temperatures.
    It also covers potential solutions and mitigation strategies."""
    
    sample_chunk = "It also covers potential solutions and mitigation strategies."

    try:
        # Create prompt
        prompt = f"""<document>
{sample_document}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{sample_chunk}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""

        print("Tokenizing input...")
        inputs = tokenizer(prompt, return_tensors="pt")
        
        print("Running inference...")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=2048,
            )
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("\nModel output:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        print("✓ Inference test completed successfully!")
        
    except Exception as e:
        print(f"✗ Error during inference: {str(e)}")


def test_system_requirements():
    """Test system requirements and available memory."""
    print("\n3. Testing system requirements")
    
    try:        
        import psutil

        # Check available RAM
        available_ram = psutil.virtual_memory().available / (1024 ** 3)  # Convert to GB
        print(f"Available RAM: {available_ram:.2f} GB")
        
        if available_ram < 8:
            print("⚠️ Warning: Less than 8GB RAM available. You might experience performance issues.")
        else:
            print("✓ Sufficient RAM available")
            
        # Check if CUDA is available
        cuda_available = torch.cuda.is_available()
        print(f"CUDA available: {'✓ Yes' if cuda_available else '✗ No'}")
   
        if not cuda_available:
            print("Note: Running on CPU. Processing will be slower.")
            
    except Exception as e:
        print(f"Error checking system requirements: {str(e)}")


def main():
    print("Starting model and inference tests...")

    # Login to Hugging Face Hub
    login()

    # Test system requirements first
    test_system_requirements()
    
    # Test model setup
    model, tokenizer = test_model_setup()
    if model is not None and tokenizer is not None:
        # Test inference
        test_inference(model, tokenizer)
    
    print("\nTest complete!")


if __name__ == "__main__":
    main()

